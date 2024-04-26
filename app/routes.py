from datetime import datetime
import os
import io
from flask import render_template, flash, redirect, session, url_for, request, g, send_file
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from flask_babel import _, get_locale
from app import app, db
from app.forms import LoginForm, NewsForm, RegistrationForm, EditProfileForm, PostForm, \
    ResetPasswordRequestForm, ResetPasswordForm, LikeForm
from app.models import News, Tag, User, Post, BANTag, Liked
from app.email import send_password_reset_email
from werkzeug.utils import secure_filename
from PIL import Image
from flask_ckeditor import CKEditor


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    g.locale = str(get_locale())


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = NewsForm()
    if form.validate_on_submit():
        image = request.files['image']
        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        tag_names = form.tags.data.split(',')
        tags = [Tag(name=name) for name in tag_names]
        news = News(title=form.title.data, content=form.content.data, image=filename, author=current_user, tags=tags)
        db.session.add(news)
        db.session.commit()
        return redirect(url_for('home'))

    # 获取所有的新闻
    news_list = News.query.all()

    # 获取所有的 BANTag 对象
    ban_tags = BANTag.query.all()

    # 创建一个包含所有被 BANTag 记录的标签的集合
    ban_tag_set = {ban_tag.tag for ban_tag in ban_tags}

    # 过滤掉那些带有被 BANTag 记录的标签的新闻
    news_list = [news for news in news_list if not any(tag in ban_tag_set for tag in news.tags)]

    # 过滤掉被当前用户屏蔽的新闻
    news_list = [news for news in news_list if news not in current_user.blocked_news]

    for news in news_list:
        if len(news.content) > 100:
            news.content = news.content[:100] + '...'
    return render_template('index.html.j2', form=form, news_list=news_list, user=current_user, ban_tags=ban_tags)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash(_('Invalid username or password'))
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html.j2', title=_('Sign In'), form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(_('Congratulations, you are now a registered user!'))
        return redirect(url_for('login'))
    return render_template('register.html.j2', title=_('Register'), form=form)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash(
            _('Check your email for the instructions to reset your password'))
        return redirect(url_for('login'))
    return render_template('reset_password_request.html.j2',
                           title=_('Reset Password'), form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if user is None:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash(_('Your password has been reset.'))
        return redirect(url_for('login'))
    return render_template('reset_password.html.j2', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.followed_posts().paginate(
        page=page, per_page=app.config["POSTS_PER_PAGE"], error_out=False)
    next_url = url_for(
        'index', page=posts.next_num) if posts.next_num else None
    prev_url = url_for(
        'index', page=posts.prev_num) if posts.prev_num else None
    return render_template('user.html.j2', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html.j2', title=_('Edit Profile'),
                           form=form)


@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username)s not found.', username=username))
        return redirect(url_for('index'))
    if user == current_user:
        flash(_('You cannot follow yourself!'))
        return redirect(url_for('user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash(_('You are following %(username)s!', username=username))
    return redirect(url_for('user', username=username))


@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username)s not found.', username=username))
        return redirect(url_for('index'))
    if user == current_user:
        flash(_('You cannot unfollow yourself!'))
        return redirect(url_for('user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(_('You are not following %(username)s.', username=username))
    return redirect(url_for('user', username=username))

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        query = request.form['query']
        if query: 
            results = News.query.filter(News.title.contains(query)).all()
            return render_template('search.html', results=results)
        else:
            return render_template('search.html', message="You did not enter any search terms.")
    return render_template('search.html')


def perform_search(query):
    results = [f"Result for '{query}': {i}" for i in range(3)]
    return results

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    form = NewsForm()
    if request.method == "POST":
        if 'editor' in request.form:
            user = current_user
            image = request.files['image']
            image_data = image.read()
            tag_names = request.form.getlist('tags')
            if not tag_names or all(name == '' for name in tag_names):
                return "<script>alert('Tags cannot be empty. Please enter at least one tag.'); window.location = '/submit';</script>"
            tags = []
            for name in tag_names:
                name = '#' + name
                tag = Tag.query.filter_by(name=name).first()
                if tag is None:
                    tag = Tag(name=name)
                tags.append(tag)
            news = News(title=form.title.data, author=user, image=image_data, content=request.form['editor'], tags=tags)
            db.session.add(news)
            db.session.commit()
            return redirect(url_for('index'))
    else:
        news = News()
        news.tags = []
        return render_template('submit.html', form=form, news=news)


@app.route('/edit/<int:news_id>', methods=['GET', 'POST'])
def edit(news_id):
    news = News.query.get(news_id)
    if current_user.username != news.author.username:
        return "You are not authorized to edit this news."
    form = NewsForm()
    if request.method == "POST":
        if 'editor' in request.form:
            news.title = form.title.data
            news.content = request.form['editor']
            if 'tags' in request.form and request.form['tags'] != '':
                tag_names = request.form.getlist('tags')
                if not tag_names or all(name == '' for name in tag_names):
                    return "<script>alert('Tags cannot be empty. Please enter at least one tag.'); window.location = '/edit/" + str(news_id) + "';</script>"
                tags = []
                for name in tag_names:
                    name = '#' + name
                    tag = Tag.query.filter_by(name=name).first()
                    if tag is None:
                        tag = Tag(name=name)
                    tags.append(tag)
                if tags:
                    news.tags = tags
            if 'image' in request.files and request.files['image'].filename != '':
                news.image = request.files['image'].read()
            db.session.commit()
            return redirect(url_for('index'))
    else:
        form.title.data = news.title
        form.content.data = news.content
        news_tags = [tag.name for tag in news.tags]
        return render_template('submit.html', form=form, news=news, news_tags=news_tags)


@app.route('/picture/<int:news_id>')    #图片解码
def picture(news_id):
    news = News.query.get(news_id)
    if news and news.image:
        return send_file(io.BytesIO(news.image), mimetype='image/jpg')
    

@app.route('/news/<int:news_id>', methods=['GET', 'POST'])#新闻主页

def news_detail(news_id):
    page = request.args.get('page', 1, type=int)
    form = PostForm()
    like_form = LikeForm()  # 新增的点赞表单
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user, news_id=news_id)
        db.session.add(post)
        db.session.commit()
        flash(_('Your post is now live!'))
    elif like_form.validate_on_submit():  # 处理点赞表单提交
        liked = Liked.query.filter_by(user_id=current_user.id, news_id=news_id).first()
        if not liked:  # 如果用户没有点过赞
            liked = Liked(user_id=current_user.id, news_id=news_id)
            db.session.add(liked)
            news = News.query.get(news_id)
            news.number_like += 1  # 点赞数加一
            db.session.commit()
    news = News.query.get(news_id)
    posts = Post.query.filter_by(news_id=news_id).order_by(Post.timestamp.desc()).paginate(page=page, per_page=app.config["POSTS_PER_PAGE"], error_out=False)
    next_url = url_for('news_detail', news_id=news_id, page=posts.next_num) if posts.has_next else None
    prev_url = url_for('news_detail', news_id=news_id, page=posts.prev_num) if posts.has_prev else None
    return render_template('fakenews.html.j2', news=news,
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url, form=form, like_form=like_form)  # 将点赞表单传递给模板



@app.route('/delete/<int:news_id>', methods=['POST'])
@login_required
def delete_news(news_id):
    news = News.query.get(news_id)
    if news is None:
        abort(404)
    if news.author != current_user:
        flash("You are not authorized to delete this news.")
        return redirect(url_for('news_detail', news_id=news.id))
    db.session.delete(news)
    db.session.commit()
    flash("News deleted successfully.")
    return redirect(url_for('index'))


@app.route('/BAN_tags', methods=['GET', 'POST'])
@login_required
def BAN_tags():
    tag_id = request.args.get('tag_id', type=int)
    news_id = request.args.get('news_id', type=int)
    ban_tag = BANTag(tag_id=tag_id, news_id=news_id, user_id=current_user.id)
    db.session.add(ban_tag)
    db.session.commit()
    ban_tags = BANTag.query.all()
    return render_template('BAN_tags.html.j2', ban_tags=ban_tags)


@app.route('/delete_ban_tag/<int:ban_tag_id>', methods=['POST'])
@login_required
def delete_ban_tag(ban_tag_id):
    ban_tag = BANTag.query.get(ban_tag_id)
    if ban_tag is not None:
        db.session.delete(ban_tag)
        db.session.commit()
    ban_tags = BANTag.query.all()  # 重新获取所有的ban_tags
    return render_template('BAN_tags.html.j2', ban_tags=ban_tags)  # 用更新后的ban_tags渲染模板


@app.route('/block/<int:news_id>')
def block(news_id):
    news = News.query.get(news_id)
    if news is not None:
        if current_user == news.author:
            flash("You can't shield yourself.")
            return redirect(url_for('index'))
        else:
            current_user.blocked_news.append(news)
            db.session.commit()
            return redirect(url_for('index'))
    return redirect(url_for('index'))


