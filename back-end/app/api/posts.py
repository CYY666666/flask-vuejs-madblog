from flask import request, jsonify, url_for, g, abort

from app.api import bp
from app.api.auth import token_auth
from app.api.errors import error_response, bad_request
from app.models import Post


@bp.route('/posts', methods=['POST'])
@token_auth.login_required
def create_post():
    '''添加一篇新文章'''
    data = request.get_json()
    if not data:
        return bad_request('You must post JSON data.')
    message = {}
    if 'title' not in data or not data.get('title', None):
        message['title'] = 'Title is required.'
    elif len(data.get('title')) > 255:
        message['title'] = 'Title must less than 255 characters.'
    if 'body' not in data or not data.get('body'):
        message['body'] = 'Body is required.'
    if message:
        return bad_request(message)

    post = Post()
    post.from_dict(data)
    post.author = g.current_user
    post.save()
    response = jsonify(post.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_post', id=post.id)
    return response


@bp.route('/posts', methods=['GET'])
def get_posts():
    '''返回文章集合，分页'''
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 1000)
    data = Post.to_collection_dict(Post.select().order_by(Post.timestamp.desc()), page, per_page, 'api.get_posts')
    return jsonify(data)


@bp.route('/posts/<int:id>', methods=['GET'])
def get_post(id):
    '''返回一篇文章'''
    post = Post.get_or_none(id)
    if not post:
        abort(404)
    post.views +=1
    post.save()
    return jsonify(post.to_dict())


@bp.route('/posts/<int:id>', methods=['PUT'])
@token_auth.login_required
def update_post(id):
    '''修改一篇文章'''
    post = Post.get_or_none(id)
    if post == None:
        abort(404)
    if g.current_user != post.author:
        return error_response(403)

    data = request.get_json()
    if not data:
        return bad_request('You must post JSON data.')
    message = {}
    if 'title' not in data or not data.get('title'):
        message['title'] = 'Title is required.'
    elif len(data.get('title')) > 255:
        message['title'] = 'Title must less than 255 characters.'
    if 'body' not in data or not data.get('body'):
        message['body'] = 'Body is required.'
    if message:
        return bad_request(message)

    post.from_dict(data)
    post.save()
    return jsonify(post.to_dict())


@bp.route('/posts/<int:id>', methods=['DELETE'])
@token_auth.login_required
def delete_post(id):
    '''删除一篇文章'''
    post = Post.get_or_none(id)
    if not post:
        abort(404)
    if g.current_user != post.author:
        return error_response(403)
    post.delete_instance(recursive=False)
    post.save()
    return '', 204