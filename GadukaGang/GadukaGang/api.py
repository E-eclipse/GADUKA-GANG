from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.db import IntegrityError
import json
from .models import (
    User, UserProfile, Section, Topic, Post, Achievement, UserAchievement,
    UserRank, UserRankProgress, Tag, TopicTag, Certificate, UserCertificate,
    Complaint, Chat, ChatParticipant, ChatMessage, SystemLog, ForumSetting,
    PostLike, TopicRating, UserSubscription, TopicSubscription, ModeratorAction,
    AdminLog, Notification, SearchIndex, GitHubAuth, TopicView
)


def api_documentation(request):
    """Страница документации API"""
    endpoints = [
        {'name': 'User', 'list': '/api/users/', 'detail': '/api/users/{id}/'},
        {'name': 'UserProfile', 'list': '/api/userprofiles/', 'detail': '/api/userprofiles/{user_id}/'},
        {'name': 'Section', 'list': '/api/sections/', 'detail': '/api/sections/{id}/'},
        {'name': 'Topic', 'list': '/api/topics/', 'detail': '/api/topics/{id}/'},
        {'name': 'Post', 'list': '/api/posts/', 'detail': '/api/posts/{id}/'},
        {'name': 'Achievement', 'list': '/api/achievements/', 'detail': '/api/achievements/{id}/'},
        {'name': 'UserAchievement', 'list': '/api/userachievements/', 'detail': '/api/userachievements/{id}/'},
        {'name': 'UserRank', 'list': '/api/userranks/', 'detail': '/api/userranks/{id}/'},
        {'name': 'UserRankProgress', 'list': '/api/userrankprogresses/', 'detail': '/api/userrankprogresses/{user_id}/'},
        {'name': 'Tag', 'list': '/api/tags/', 'detail': '/api/tags/{id}/'},
        {'name': 'TopicTag', 'list': '/api/topictags/', 'detail': '/api/topictags/{id}/'},
        {'name': 'Certificate', 'list': '/api/certificates/', 'detail': '/api/certificates/{id}/'},
        {'name': 'UserCertificate', 'list': '/api/usercertificates/', 'detail': '/api/usercertificates/{id}/'},
        {'name': 'Complaint', 'list': '/api/complaints/', 'detail': '/api/complaints/{id}/'},
        {'name': 'Chat', 'list': '/api/chats/', 'detail': '/api/chats/{id}/'},
        {'name': 'ChatParticipant', 'list': '/api/chatparticipants/', 'detail': '/api/chatparticipants/{id}/'},
        {'name': 'ChatMessage', 'list': '/api/chatmessages/', 'detail': '/api/chatmessages/{id}/'},
        {'name': 'SystemLog', 'list': '/api/systemlogs/', 'detail': '/api/systemlogs/{id}/'},
        {'name': 'ForumSetting', 'list': '/api/forumsettings/', 'detail': '/api/forumsettings/{id}/'},
        {'name': 'PostLike', 'list': '/api/postlikes/', 'detail': '/api/postlikes/{id}/'},
        {'name': 'TopicRating', 'list': '/api/topicratings/', 'detail': '/api/topicratings/{id}/'},
        {'name': 'UserSubscription', 'list': '/api/usersubscriptions/', 'detail': '/api/usersubscriptions/{id}/'},
        {'name': 'TopicSubscription', 'list': '/api/topicsubscriptions/', 'detail': '/api/topicsubscriptions/{id}/'},
        {'name': 'ModeratorAction', 'list': '/api/moderatoractions/', 'detail': '/api/moderatoractions/{id}/'},
        {'name': 'AdminLog', 'list': '/api/adminlogs/', 'detail': '/api/adminlogs/{id}/'},
        {'name': 'Notification', 'list': '/api/notifications/', 'detail': '/api/notifications/{id}/'},
        {'name': 'SearchIndex', 'list': '/api/searchindices/', 'detail': '/api/searchindices/{id}/'},
        {'name': 'GitHubAuth', 'list': '/api/githubauths/', 'detail': '/api/githubauths/{user_id}/'},
        {'name': 'TopicView', 'list': '/api/topicviews/', 'detail': '/api/topicviews/{id}/'},
    ]
    
    context = {
        'endpoints': endpoints,
    }
    return render(request, 'api_documentation.html', context)


def serialize_model(obj, fields):
    """Сериализация модели в словарь"""
    data = {}
    for field in fields:
        value = getattr(obj, field, None)
        if hasattr(value, 'id'):
            data[field] = value.id
        elif hasattr(value, 'isoformat'):
            data[field] = value.isoformat()
        else:
            data[field] = value
    return data


def get_model_fields(model_class):
    """Получить список полей модели"""
    return [f.name for f in model_class._meta.get_fields() if not f.many_to_many and not f.one_to_many]


# User API
@csrf_exempt
@require_http_methods(["GET", "POST"])
def user_list_create(request):
    if request.method == 'GET':
        users = User.objects.all()
        data = []
        for user in users:
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'registration_date': user.registration_date.isoformat() if user.registration_date else None,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'is_active': user.is_active,
            }
            data.append(user_data)
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            user = User.objects.create_user(
                username=data.get('username'),
                email=data.get('email'),
                password=data.get('password', 'defaultpassword123'),
                role=data.get('role', 'user'),
            )
            return JsonResponse({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def user_detail(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    
    if request.method == 'GET':
        return JsonResponse({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'registration_date': user.registration_date.isoformat() if user.registration_date else None,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'is_active': user.is_active,
        })
    
    elif request.method == 'DELETE':
        user.delete()
        return JsonResponse({'message': 'User deleted successfully'}, status=200)


# UserProfile API
@csrf_exempt
@require_http_methods(["GET", "POST"])
def userprofile_list_create(request):
    if request.method == 'GET':
        profiles = UserProfile.objects.all()
        data = []
        for profile in profiles:
            data.append({
                'user_id': profile.user_id,
                'avatar_url': profile.avatar_url,
                'bio': profile.bio,
                'signature': profile.signature,
                'post_count': profile.post_count,
                'join_date': profile.join_date.isoformat(),
                'last_activity': profile.last_activity.isoformat(),
            })
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            user = User.objects.get(id=data['user_id'])
            profile = UserProfile.objects.create(
                user=user,
                avatar_url=data.get('avatar_url', ''),
                bio=data.get('bio', ''),
                signature=data.get('signature', ''),
                post_count=data.get('post_count', 0),
            )
            return JsonResponse({
                'user_id': profile.user_id,
                'avatar_url': profile.avatar_url,
                'bio': profile.bio,
                'signature': profile.signature,
                'post_count': profile.post_count,
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def userprofile_detail(request, user_id):
    try:
        profile = UserProfile.objects.get(user_id=user_id)
    except UserProfile.DoesNotExist:
        return JsonResponse({'error': 'UserProfile not found'}, status=404)
    
    if request.method == 'GET':
        return JsonResponse({
            'user_id': profile.user_id,
            'avatar_url': profile.avatar_url,
            'bio': profile.bio,
            'signature': profile.signature,
            'post_count': profile.post_count,
            'join_date': profile.join_date.isoformat(),
            'last_activity': profile.last_activity.isoformat(),
        })
    
    elif request.method == 'DELETE':
        profile.delete()
        return JsonResponse({'message': 'UserProfile deleted successfully'}, status=200)


# Section API
@csrf_exempt
@require_http_methods(["GET", "POST"])
def section_list_create(request):
    if request.method == 'GET':
        sections = Section.objects.all()
        data = []
        for section in sections:
            data.append({
                'id': section.id,
                'name': section.name,
                'description': section.description,
                'created_by_id': section.created_by_id,
                'created_date': section.created_date.isoformat(),
            })
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            created_by = None
            if data.get('created_by_id'):
                created_by = User.objects.get(id=data['created_by_id'])
            section = Section.objects.create(
                name=data['name'],
                description=data['description'],
                created_by=created_by,
            )
            return JsonResponse({
                'id': section.id,
                'name': section.name,
                'description': section.description,
                'created_by_id': section.created_by_id,
                'created_date': section.created_date.isoformat(),
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def section_detail(request, section_id):
    try:
        section = Section.objects.get(id=section_id)
    except Section.DoesNotExist:
        return JsonResponse({'error': 'Section not found'}, status=404)
    
    if request.method == 'GET':
        return JsonResponse({
            'id': section.id,
            'name': section.name,
            'description': section.description,
            'created_by_id': section.created_by_id,
            'created_date': section.created_date.isoformat(),
        })
    
    elif request.method == 'DELETE':
        section.delete()
        return JsonResponse({'message': 'Section deleted successfully'}, status=200)


# Topic API
@csrf_exempt
@require_http_methods(["GET", "POST"])
def topic_list_create(request):
    if request.method == 'GET':
        topics = Topic.objects.all()
        data = []
        for topic in topics:
            data.append({
                'id': topic.id,
                'section_id': topic.section_id,
                'title': topic.title,
                'author_id': topic.author_id,
                'created_date': topic.created_date.isoformat(),
                'last_post_date': topic.last_post_date.isoformat(),
                'is_pinned': topic.is_pinned,
                'view_count': topic.view_count,
                'average_rating': topic.average_rating,
                'rating_count': topic.rating_count,
            })
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            section = Section.objects.get(id=data['section_id'])
            author = User.objects.get(id=data['author_id'])
            topic = Topic.objects.create(
                section=section,
                title=data['title'],
                author=author,
                is_pinned=data.get('is_pinned', False),
                view_count=data.get('view_count', 0),
            )
            return JsonResponse({
                'id': topic.id,
                'section_id': topic.section_id,
                'title': topic.title,
                'author_id': topic.author_id,
                'created_date': topic.created_date.isoformat(),
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def topic_detail(request, topic_id):
    try:
        topic = Topic.objects.get(id=topic_id)
    except Topic.DoesNotExist:
        return JsonResponse({'error': 'Topic not found'}, status=404)
    
    if request.method == 'GET':
        return JsonResponse({
            'id': topic.id,
            'section_id': topic.section_id,
            'title': topic.title,
            'author_id': topic.author_id,
            'created_date': topic.created_date.isoformat(),
            'last_post_date': topic.last_post_date.isoformat(),
            'is_pinned': topic.is_pinned,
            'view_count': topic.view_count,
            'average_rating': topic.average_rating,
            'rating_count': topic.rating_count,
        })
    
    elif request.method == 'DELETE':
        topic.delete()
        return JsonResponse({'message': 'Topic deleted successfully'}, status=200)


# Post API
@csrf_exempt
@require_http_methods(["GET", "POST"])
def post_list_create(request):
    if request.method == 'GET':
        posts = Post.objects.all()
        data = []
        for post in posts:
            data.append({
                'id': post.id,
                'topic_id': post.topic_id,
                'author_id': post.author_id,
                'content': post.content,
                'created_date': post.created_date.isoformat(),
                'last_edited_date': post.last_edited_date.isoformat() if post.last_edited_date else None,
                'edit_count': post.edit_count,
                'is_deleted': post.is_deleted,
                'like_count': post.like_count,
                'dislike_count': post.dislike_count,
            })
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            topic = Topic.objects.get(id=data['topic_id'])
            author = User.objects.get(id=data['author_id'])
            post = Post.objects.create(
                topic=topic,
                author=author,
                content=data['content'],
                is_deleted=data.get('is_deleted', False),
            )
            return JsonResponse({
                'id': post.id,
                'topic_id': post.topic_id,
                'author_id': post.author_id,
                'content': post.content,
                'created_date': post.created_date.isoformat(),
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def post_detail(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return JsonResponse({'error': 'Post not found'}, status=404)
    
    if request.method == 'GET':
        return JsonResponse({
            'id': post.id,
            'topic_id': post.topic_id,
            'author_id': post.author_id,
            'content': post.content,
            'created_date': post.created_date.isoformat(),
            'last_edited_date': post.last_edited_date.isoformat() if post.last_edited_date else None,
            'edit_count': post.edit_count,
            'is_deleted': post.is_deleted,
            'like_count': post.like_count,
            'dislike_count': post.dislike_count,
        })
    
    elif request.method == 'DELETE':
        post.delete()
        return JsonResponse({'message': 'Post deleted successfully'}, status=200)


# Achievement API
@csrf_exempt
@require_http_methods(["GET", "POST"])
def achievement_list_create(request):
    if request.method == 'GET':
        achievements = Achievement.objects.all()
        data = []
        for achievement in achievements:
            data.append({
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'icon_url': achievement.icon_url,
                'criteria': achievement.criteria,
            })
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            achievement = Achievement.objects.create(
                name=data['name'],
                description=data['description'],
                icon_url=data.get('icon_url', ''),
                criteria=data.get('criteria', {}),
            )
            return JsonResponse({
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'icon_url': achievement.icon_url,
                'criteria': achievement.criteria,
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def achievement_detail(request, achievement_id):
    try:
        achievement = Achievement.objects.get(id=achievement_id)
    except Achievement.DoesNotExist:
        return JsonResponse({'error': 'Achievement not found'}, status=404)
    
    if request.method == 'GET':
        return JsonResponse({
            'id': achievement.id,
            'name': achievement.name,
            'description': achievement.description,
            'icon_url': achievement.icon_url,
            'criteria': achievement.criteria,
        })
    
    elif request.method == 'DELETE':
        achievement.delete()
        return JsonResponse({'message': 'Achievement deleted successfully'}, status=200)


# UserAchievement API
@csrf_exempt
@require_http_methods(["GET", "POST"])
def userachievement_list_create(request):
    if request.method == 'GET':
        user_achievements = UserAchievement.objects.all()
        data = []
        for ua in user_achievements:
            data.append({
                'id': ua.id,
                'user_id': ua.user_id,
                'achievement_id': ua.achievement_id,
                'earned_date': ua.earned_date.isoformat(),
                'awarded_by_id': ua.awarded_by_id,
            })
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            user = User.objects.get(id=data['user_id'])
            achievement = Achievement.objects.get(id=data['achievement_id'])
            awarded_by = None
            if data.get('awarded_by_id'):
                awarded_by = User.objects.get(id=data['awarded_by_id'])
            user_achievement = UserAchievement.objects.create(
                user=user,
                achievement=achievement,
                awarded_by=awarded_by,
            )
            return JsonResponse({
                'id': user_achievement.id,
                'user_id': user_achievement.user_id,
                'achievement_id': user_achievement.achievement_id,
                'earned_date': user_achievement.earned_date.isoformat(),
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def userachievement_detail(request, userachievement_id):
    try:
        user_achievement = UserAchievement.objects.get(id=userachievement_id)
    except UserAchievement.DoesNotExist:
        return JsonResponse({'error': 'UserAchievement not found'}, status=404)
    
    if request.method == 'GET':
        return JsonResponse({
            'id': user_achievement.id,
            'user_id': user_achievement.user_id,
            'achievement_id': user_achievement.achievement_id,
            'earned_date': user_achievement.earned_date.isoformat(),
            'awarded_by_id': user_achievement.awarded_by_id,
        })
    
    elif request.method == 'DELETE':
        user_achievement.delete()
        return JsonResponse({'message': 'UserAchievement deleted successfully'}, status=200)


# UserRank API
@csrf_exempt
@require_http_methods(["GET", "POST"])
def userrank_list_create(request):
    if request.method == 'GET':
        ranks = UserRank.objects.all()
        data = []
        for rank in ranks:
            data.append({
                'id': rank.id,
                'name': rank.name,
                'required_points': rank.required_points,
                'icon_url': rank.icon_url,
            })
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            rank = UserRank.objects.create(
                name=data['name'],
                required_points=data['required_points'],
                icon_url=data.get('icon_url', ''),
            )
            return JsonResponse({
                'id': rank.id,
                'name': rank.name,
                'required_points': rank.required_points,
                'icon_url': rank.icon_url,
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def userrank_detail(request, userrank_id):
    try:
        rank = UserRank.objects.get(id=userrank_id)
    except UserRank.DoesNotExist:
        return JsonResponse({'error': 'UserRank not found'}, status=404)
    
    if request.method == 'GET':
        return JsonResponse({
            'id': rank.id,
            'name': rank.name,
            'required_points': rank.required_points,
            'icon_url': rank.icon_url,
        })
    
    elif request.method == 'DELETE':
        rank.delete()
        return JsonResponse({'message': 'UserRank deleted successfully'}, status=200)


# UserRankProgress API
@csrf_exempt
@require_http_methods(["GET", "POST"])
def userrankprogress_list_create(request):
    if request.method == 'GET':
        progresses = UserRankProgress.objects.all()
        data = []
        for progress in progresses:
            data.append({
                'user_id': progress.user_id,
                'rank_id': progress.rank_id,
                'current_points': progress.current_points,
                'progress_percentage': progress.progress_percentage,
            })
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            user = User.objects.get(id=data['user_id'])
            rank = None
            if data.get('rank_id'):
                rank = UserRank.objects.get(id=data['rank_id'])
            progress = UserRankProgress.objects.create(
                user=user,
                rank=rank,
                current_points=data.get('current_points', 0),
                progress_percentage=data.get('progress_percentage', 0),
            )
            return JsonResponse({
                'user_id': progress.user_id,
                'rank_id': progress.rank_id,
                'current_points': progress.current_points,
                'progress_percentage': progress.progress_percentage,
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def userrankprogress_detail(request, user_id):
    try:
        progress = UserRankProgress.objects.get(user_id=user_id)
    except UserRankProgress.DoesNotExist:
        return JsonResponse({'error': 'UserRankProgress not found'}, status=404)
    
    if request.method == 'GET':
        return JsonResponse({
            'user_id': progress.user_id,
            'rank_id': progress.rank_id,
            'current_points': progress.current_points,
            'progress_percentage': progress.progress_percentage,
        })
    
    elif request.method == 'DELETE':
        progress.delete()
        return JsonResponse({'message': 'UserRankProgress deleted successfully'}, status=200)


# Tag API
@csrf_exempt
@require_http_methods(["GET", "POST"])
def tag_list_create(request):
    if request.method == 'GET':
        tags = Tag.objects.all()
        data = []
        for tag in tags:
            data.append({
                'id': tag.id,
                'name': tag.name,
                'color': tag.color,
            })
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            tag = Tag.objects.create(
                name=data['name'],
                color=data.get('color', '#000000'),
            )
            return JsonResponse({
                'id': tag.id,
                'name': tag.name,
                'color': tag.color,
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def tag_detail(request, tag_id):
    try:
        tag = Tag.objects.get(id=tag_id)
    except Tag.DoesNotExist:
        return JsonResponse({'error': 'Tag not found'}, status=404)
    
    if request.method == 'GET':
        return JsonResponse({
            'id': tag.id,
            'name': tag.name,
            'color': tag.color,
        })
    
    elif request.method == 'DELETE':
        tag.delete()
        return JsonResponse({'message': 'Tag deleted successfully'}, status=200)


# TopicTag API
@csrf_exempt
@require_http_methods(["GET", "POST"])
def topictag_list_create(request):
    if request.method == 'GET':
        topic_tags = TopicTag.objects.all()
        data = []
        for tt in topic_tags:
            data.append({
                'id': tt.id,
                'topic_id': tt.topic_id,
                'tag_id': tt.tag_id,
            })
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            topic = Topic.objects.get(id=data['topic_id'])
            tag = Tag.objects.get(id=data['tag_id'])
            topic_tag = TopicTag.objects.create(
                topic=topic,
                tag=tag,
            )
            return JsonResponse({
                'id': topic_tag.id,
                'topic_id': topic_tag.topic_id,
                'tag_id': topic_tag.tag_id,
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def topictag_detail(request, topictag_id):
    try:
        topic_tag = TopicTag.objects.get(id=topictag_id)
    except TopicTag.DoesNotExist:
        return JsonResponse({'error': 'TopicTag not found'}, status=404)
    
    if request.method == 'GET':
        return JsonResponse({
            'id': topic_tag.id,
            'topic_id': topic_tag.topic_id,
            'tag_id': topic_tag.tag_id,
        })
    
    elif request.method == 'DELETE':
        topic_tag.delete()
        return JsonResponse({'message': 'TopicTag deleted successfully'}, status=200)


# Certificate API
@csrf_exempt
@require_http_methods(["GET", "POST"])
def certificate_list_create(request):
    if request.method == 'GET':
        certificates = Certificate.objects.all()
        data = []
        for cert in certificates:
            data.append({
                'id': cert.id,
                'name': cert.name,
                'description': cert.description,
                'template_url': cert.template_url,
                'criteria': cert.criteria,
            })
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            certificate = Certificate.objects.create(
                name=data['name'],
                description=data['description'],
                template_url=data.get('template_url', ''),
                criteria=data.get('criteria', {}),
            )
            return JsonResponse({
                'id': certificate.id,
                'name': certificate.name,
                'description': certificate.description,
                'template_url': certificate.template_url,
                'criteria': certificate.criteria,
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def certificate_detail(request, certificate_id):
    try:
        certificate = Certificate.objects.get(id=certificate_id)
    except Certificate.DoesNotExist:
        return JsonResponse({'error': 'Certificate not found'}, status=404)
    
    if request.method == 'GET':
        return JsonResponse({
            'id': certificate.id,
            'name': certificate.name,
            'description': certificate.description,
            'template_url': certificate.template_url,
            'criteria': certificate.criteria,
        })
    
    elif request.method == 'DELETE':
        certificate.delete()
        return JsonResponse({'message': 'Certificate deleted successfully'}, status=200)


# UserCertificate API
@csrf_exempt
@require_http_methods(["GET", "POST"])
def usercertificate_list_create(request):
    if request.method == 'GET':
        user_certificates = UserCertificate.objects.all()
        data = []
        for uc in user_certificates:
            data.append({
                'id': uc.id,
                'user_id': uc.user_id,
                'certificate_id': uc.certificate_id,
                'awarded_date': uc.awarded_date.isoformat(),
                'awarded_by_id': uc.awarded_by_id,
                'expiration_date': uc.expiration_date.isoformat() if uc.expiration_date else None,
            })
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            user = User.objects.get(id=data['user_id'])
            certificate = Certificate.objects.get(id=data['certificate_id'])
            awarded_by = None
            if data.get('awarded_by_id'):
                awarded_by = User.objects.get(id=data['awarded_by_id'])
            user_certificate = UserCertificate.objects.create(
                user=user,
                certificate=certificate,
                awarded_by=awarded_by,
            )
            if data.get('expiration_date'):
                from django.utils.dateparse import parse_datetime
                user_certificate.expiration_date = parse_datetime(data['expiration_date'])
                user_certificate.save()
            return JsonResponse({
                'id': user_certificate.id,
                'user_id': user_certificate.user_id,
                'certificate_id': user_certificate.certificate_id,
                'awarded_date': user_certificate.awarded_date.isoformat(),
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def usercertificate_detail(request, usercertificate_id):
    try:
        user_certificate = UserCertificate.objects.get(id=usercertificate_id)
    except UserCertificate.DoesNotExist:
        return JsonResponse({'error': 'UserCertificate not found'}, status=404)
    
    if request.method == 'GET':
        return JsonResponse({
            'id': user_certificate.id,
            'user_id': user_certificate.user_id,
            'certificate_id': user_certificate.certificate_id,
            'awarded_date': user_certificate.awarded_date.isoformat(),
            'awarded_by_id': user_certificate.awarded_by_id,
            'expiration_date': user_certificate.expiration_date.isoformat() if user_certificate.expiration_date else None,
        })
    
    elif request.method == 'DELETE':
        user_certificate.delete()
        return JsonResponse({'message': 'UserCertificate deleted successfully'}, status=200)


# Complaint API
@csrf_exempt
@require_http_methods(["GET", "POST"])
def complaint_list_create(request):
    if request.method == 'GET':
        complaints = Complaint.objects.all()
        data = []
        for complaint in complaints:
            data.append({
                'id': complaint.id,
                'reporter_id': complaint.reporter_id,
                'target_type': complaint.target_type,
                'target_id': complaint.target_id,
                'reason': complaint.reason,
                'description': complaint.description,
                'status': complaint.status,
                'assigned_moderator_id': complaint.assigned_moderator_id,
                'created_date': complaint.created_date.isoformat(),
                'resolved_date': complaint.resolved_date.isoformat() if complaint.resolved_date else None,
            })
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            reporter = User.objects.get(id=data['reporter_id'])
            assigned_moderator = None
            if data.get('assigned_moderator_id'):
                assigned_moderator = User.objects.get(id=data['assigned_moderator_id'])
            complaint = Complaint.objects.create(
                reporter=reporter,
                target_type=data['target_type'],
                target_id=data['target_id'],
                reason=data['reason'],
                description=data['description'],
                status=data.get('status', 'open'),
                assigned_moderator=assigned_moderator,
            )
            return JsonResponse({
                'id': complaint.id,
                'reporter_id': complaint.reporter_id,
                'target_type': complaint.target_type,
                'target_id': complaint.target_id,
                'status': complaint.status,
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def complaint_detail(request, complaint_id):
    try:
        complaint = Complaint.objects.get(id=complaint_id)
    except Complaint.DoesNotExist:
        return JsonResponse({'error': 'Complaint not found'}, status=404)
    
    if request.method == 'GET':
        return JsonResponse({
            'id': complaint.id,
            'reporter_id': complaint.reporter_id,
            'target_type': complaint.target_type,
            'target_id': complaint.target_id,
            'reason': complaint.reason,
            'description': complaint.description,
            'status': complaint.status,
            'assigned_moderator_id': complaint.assigned_moderator_id,
            'created_date': complaint.created_date.isoformat(),
            'resolved_date': complaint.resolved_date.isoformat() if complaint.resolved_date else None,
        })
    
    elif request.method == 'DELETE':
        complaint.delete()
        return JsonResponse({'message': 'Complaint deleted successfully'}, status=200)


# Chat API
@csrf_exempt
@require_http_methods(["GET", "POST"])
def chat_list_create(request):
    if request.method == 'GET':
        chats = Chat.objects.all()
        data = []
        for chat in chats:
            data.append({
                'id': chat.id,
                'name': chat.name,
                'chat_type': chat.chat_type,
                'created_by_id': chat.created_by_id,
                'created_date': chat.created_date.isoformat(),
                'is_active': chat.is_active,
            })
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            created_by = None
            if data.get('created_by_id'):
                created_by = User.objects.get(id=data['created_by_id'])
            chat = Chat.objects.create(
                name=data.get('name', ''),
                chat_type=data['chat_type'],
                created_by=created_by,
                is_active=data.get('is_active', True),
            )
            return JsonResponse({
                'id': chat.id,
                'name': chat.name,
                'chat_type': chat.chat_type,
                'created_by_id': chat.created_by_id,
                'created_date': chat.created_date.isoformat(),
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def chat_detail(request, chat_id):
    try:
        chat = Chat.objects.get(id=chat_id)
    except Chat.DoesNotExist:
        return JsonResponse({'error': 'Chat not found'}, status=404)
    
    if request.method == 'GET':
        return JsonResponse({
            'id': chat.id,
            'name': chat.name,
            'chat_type': chat.chat_type,
            'created_by_id': chat.created_by_id,
            'created_date': chat.created_date.isoformat(),
            'is_active': chat.is_active,
        })
    
    elif request.method == 'DELETE':
        chat.delete()
        return JsonResponse({'message': 'Chat deleted successfully'}, status=200)


# ChatParticipant API
@csrf_exempt
@require_http_methods(["GET", "POST"])
def chatparticipant_list_create(request):
    if request.method == 'GET':
        participants = ChatParticipant.objects.all()
        data = []
        for participant in participants:
            data.append({
                'id': participant.id,
                'chat_id': participant.chat_id,
                'user_id': participant.user_id,
                'joined_date': participant.joined_date.isoformat(),
                'left_date': participant.left_date.isoformat() if participant.left_date else None,
                'role_in_chat': participant.role_in_chat,
            })
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            chat = Chat.objects.get(id=data['chat_id'])
            user = User.objects.get(id=data['user_id'])
            participant = ChatParticipant.objects.create(
                chat=chat,
                user=user,
                role_in_chat=data.get('role_in_chat', 'member'),
            )
            return JsonResponse({
                'id': participant.id,
                'chat_id': participant.chat_id,
                'user_id': participant.user_id,
                'joined_date': participant.joined_date.isoformat(),
                'role_in_chat': participant.role_in_chat,
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def chatparticipant_detail(request, chatparticipant_id):
    try:
        participant = ChatParticipant.objects.get(id=chatparticipant_id)
    except ChatParticipant.DoesNotExist:
        return JsonResponse({'error': 'ChatParticipant not found'}, status=404)
    
    if request.method == 'GET':
        return JsonResponse({
            'id': participant.id,
            'chat_id': participant.chat_id,
            'user_id': participant.user_id,
            'joined_date': participant.joined_date.isoformat(),
            'left_date': participant.left_date.isoformat() if participant.left_date else None,
            'role_in_chat': participant.role_in_chat,
        })
    
    elif request.method == 'DELETE':
        participant.delete()
        return JsonResponse({'message': 'ChatParticipant deleted successfully'}, status=200)


# ChatMessage API
@csrf_exempt
@require_http_methods(["GET", "POST"])
def chatmessage_list_create(request):
    if request.method == 'GET':
        messages = ChatMessage.objects.all()
        data = []
        for message in messages:
            data.append({
                'id': message.id,
                'chat_id': message.chat_id,
                'sender_id': message.sender_id,
                'content': message.content,
                'sent_date': message.sent_date.isoformat(),
                'is_edited': message.is_edited,
                'edited_date': message.edited_date.isoformat() if message.edited_date else None,
                'is_deleted': message.is_deleted,
            })
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            chat = Chat.objects.get(id=data['chat_id'])
            sender = User.objects.get(id=data['sender_id'])
            message = ChatMessage.objects.create(
                chat=chat,
                sender=sender,
                content=data['content'],
                is_deleted=data.get('is_deleted', False),
            )
            return JsonResponse({
                'id': message.id,
                'chat_id': message.chat_id,
                'sender_id': message.sender_id,
                'content': message.content,
                'sent_date': message.sent_date.isoformat(),
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def chatmessage_detail(request, chatmessage_id):
    try:
        message = ChatMessage.objects.get(id=chatmessage_id)
    except ChatMessage.DoesNotExist:
        return JsonResponse({'error': 'ChatMessage not found'}, status=404)
    
    if request.method == 'GET':
        return JsonResponse({
            'id': message.id,
            'chat_id': message.chat_id,
            'sender_id': message.sender_id,
            'content': message.content,
            'sent_date': message.sent_date.isoformat(),
            'is_edited': message.is_edited,
            'edited_date': message.edited_date.isoformat() if message.edited_date else None,
            'is_deleted': message.is_deleted,
        })
    
    elif request.method == 'DELETE':
        message.delete()
        return JsonResponse({'message': 'ChatMessage deleted successfully'}, status=200)


# SystemLog API
@csrf_exempt
@require_http_methods(["GET", "POST"])
def systemlog_list_create(request):
    if request.method == 'GET':
        logs = SystemLog.objects.all()
        data = []
        for log in logs:
            data.append({
                'id': log.id,
                'user_id': log.user_id,
                'action_type': log.action_type,
                'action_level': log.action_level,
                'description': log.description,
                'affected_resource_type': log.affected_resource_type,
                'affected_resource_id': log.affected_resource_id,
                'timestamp': log.timestamp.isoformat(),
            })
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            user = None
            if data.get('user_id'):
                user = User.objects.get(id=data['user_id'])
            log = SystemLog.objects.create(
                user=user,
                action_type=data['action_type'],
                action_level=data['action_level'],
                description=data['description'],
                affected_resource_type=data.get('affected_resource_type', ''),
                affected_resource_id=data.get('affected_resource_id'),
            )
            return JsonResponse({
                'id': log.id,
                'user_id': log.user_id,
                'action_type': log.action_type,
                'timestamp': log.timestamp.isoformat(),
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def systemlog_detail(request, systemlog_id):
    try:
        log = SystemLog.objects.get(id=systemlog_id)
    except SystemLog.DoesNotExist:
        return JsonResponse({'error': 'SystemLog not found'}, status=404)
    
    if request.method == 'GET':
        return JsonResponse({
            'id': log.id,
            'user_id': log.user_id,
            'action_type': log.action_type,
            'action_level': log.action_level,
            'description': log.description,
            'affected_resource_type': log.affected_resource_type,
            'affected_resource_id': log.affected_resource_id,
            'timestamp': log.timestamp.isoformat(),
        })
    
    elif request.method == 'DELETE':
        log.delete()
        return JsonResponse({'message': 'SystemLog deleted successfully'}, status=200)


# ForumSetting API
@csrf_exempt
@require_http_methods(["GET", "POST"])
def forumsetting_list_create(request):
    if request.method == 'GET':
        settings = ForumSetting.objects.all()
        data = []
        for setting in settings:
            data.append({
                'id': setting.id,
                'setting_name': setting.setting_name,
                'setting_value': setting.setting_value,
                'category': setting.category,
                'last_modified': setting.last_modified.isoformat(),
                'modified_by_id': setting.modified_by_id,
            })
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            modified_by = None
            if data.get('modified_by_id'):
                modified_by = User.objects.get(id=data['modified_by_id'])
            setting = ForumSetting.objects.create(
                setting_name=data['setting_name'],
                setting_value=data.get('setting_value', {}),
                category=data['category'],
                modified_by=modified_by,
            )
            return JsonResponse({
                'id': setting.id,
                'setting_name': setting.setting_name,
                'setting_value': setting.setting_value,
                'category': setting.category,
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def forumsetting_detail(request, forumsetting_id):
    try:
        setting = ForumSetting.objects.get(id=forumsetting_id)
    except ForumSetting.DoesNotExist:
        return JsonResponse({'error': 'ForumSetting not found'}, status=404)
    
    if request.method == 'GET':
        return JsonResponse({
            'id': setting.id,
            'setting_name': setting.setting_name,
            'setting_value': setting.setting_value,
            'category': setting.category,
            'last_modified': setting.last_modified.isoformat(),
            'modified_by_id': setting.modified_by_id,
        })
    
    elif request.method == 'DELETE':
        setting.delete()
        return JsonResponse({'message': 'ForumSetting deleted successfully'}, status=200)


# PostLike API
@csrf_exempt
@require_http_methods(["GET", "POST"])
def postlike_list_create(request):
    if request.method == 'GET':
        likes = PostLike.objects.all()
        data = []
        for like in likes:
            data.append({
                'id': like.id,
                'post_id': like.post_id,
                'user_id': like.user_id,
                'like_type': like.like_type,
                'created_date': like.created_date.isoformat(),
            })
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            post = Post.objects.get(id=data['post_id'])
            user = User.objects.get(id=data['user_id'])
            like = PostLike.objects.create(
                post=post,
                user=user,
                like_type=data['like_type'],
            )
            return JsonResponse({
                'id': like.id,
                'post_id': like.post_id,
                'user_id': like.user_id,
                'like_type': like.like_type,
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def postlike_detail(request, postlike_id):
    try:
        like = PostLike.objects.get(id=postlike_id)
    except PostLike.DoesNotExist:
        return JsonResponse({'error': 'PostLike not found'}, status=404)
    
    if request.method == 'GET':
        return JsonResponse({
            'id': like.id,
            'post_id': like.post_id,
            'user_id': like.user_id,
            'like_type': like.like_type,
            'created_date': like.created_date.isoformat(),
        })
    
    elif request.method == 'DELETE':
        like.delete()
        return JsonResponse({'message': 'PostLike deleted successfully'}, status=200)


# TopicRating API
@csrf_exempt
@require_http_methods(["GET", "POST"])
def topicrating_list_create(request):
    if request.method == 'GET':
        ratings = TopicRating.objects.all()
        data = []
        for rating in ratings:
            data.append({
                'id': rating.id,
                'topic_id': rating.topic_id,
                'user_id': rating.user_id,
                'rating': rating.rating,
                'created_date': rating.created_date.isoformat(),
            })
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            topic = Topic.objects.get(id=data['topic_id'])
            user = User.objects.get(id=data['user_id'])
            rating = TopicRating.objects.create(
                topic=topic,
                user=user,
                rating=data['rating'],
            )
            return JsonResponse({
                'id': rating.id,
                'topic_id': rating.topic_id,
                'user_id': rating.user_id,
                'rating': rating.rating,
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def topicrating_detail(request, topicrating_id):
    try:
        rating = TopicRating.objects.get(id=topicrating_id)
    except TopicRating.DoesNotExist:
        return JsonResponse({'error': 'TopicRating not found'}, status=404)
    
    if request.method == 'GET':
        return JsonResponse({
            'id': rating.id,
            'topic_id': rating.topic_id,
            'user_id': rating.user_id,
            'rating': rating.rating,
            'created_date': rating.created_date.isoformat(),
        })
    
    elif request.method == 'DELETE':
        rating.delete()
        return JsonResponse({'message': 'TopicRating deleted successfully'}, status=200)


# UserSubscription API
@csrf_exempt
@require_http_methods(["GET", "POST"])
def usersubscription_list_create(request):
    if request.method == 'GET':
        subscriptions = UserSubscription.objects.all()
        data = []
        for sub in subscriptions:
            data.append({
                'id': sub.id,
                'subscriber_id': sub.subscriber_id,
                'subscribed_to_id': sub.subscribed_to_id,
                'created_date': sub.created_date.isoformat(),
            })
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            subscriber = User.objects.get(id=data['subscriber_id'])
            subscribed_to = User.objects.get(id=data['subscribed_to_id'])
            if subscriber == subscribed_to:
                return JsonResponse({'error': 'User cannot subscribe to themselves'}, status=400)
            subscription = UserSubscription.objects.create(
                subscriber=subscriber,
                subscribed_to=subscribed_to,
            )
            return JsonResponse({
                'id': subscription.id,
                'subscriber_id': subscription.subscriber_id,
                'subscribed_to_id': subscription.subscribed_to_id,
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def usersubscription_detail(request, usersubscription_id):
    try:
        subscription = UserSubscription.objects.get(id=usersubscription_id)
    except UserSubscription.DoesNotExist:
        return JsonResponse({'error': 'UserSubscription not found'}, status=404)
    
    if request.method == 'GET':
        return JsonResponse({
            'id': subscription.id,
            'subscriber_id': subscription.subscriber_id,
            'subscribed_to_id': subscription.subscribed_to_id,
            'created_date': subscription.created_date.isoformat(),
        })
    
    elif request.method == 'DELETE':
        subscription.delete()
        return JsonResponse({'message': 'UserSubscription deleted successfully'}, status=200)


# TopicSubscription API
@csrf_exempt
@require_http_methods(["GET", "POST"])
def topicsubscription_list_create(request):
    if request.method == 'GET':
        subscriptions = TopicSubscription.objects.all()
        data = []
        for sub in subscriptions:
            data.append({
                'id': sub.id,
                'topic_id': sub.topic_id,
                'user_id': sub.user_id,
                'created_date': sub.created_date.isoformat(),
                'notify_on_new_post': sub.notify_on_new_post,
            })
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            topic = Topic.objects.get(id=data['topic_id'])
            user = User.objects.get(id=data['user_id'])
            subscription = TopicSubscription.objects.create(
                topic=topic,
                user=user,
                notify_on_new_post=data.get('notify_on_new_post', True),
            )
            return JsonResponse({
                'id': subscription.id,
                'topic_id': subscription.topic_id,
                'user_id': subscription.user_id,
                'notify_on_new_post': subscription.notify_on_new_post,
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def topicsubscription_detail(request, topicsubscription_id):
    try:
        subscription = TopicSubscription.objects.get(id=topicsubscription_id)
    except TopicSubscription.DoesNotExist:
        return JsonResponse({'error': 'TopicSubscription not found'}, status=404)
    
    if request.method == 'GET':
        return JsonResponse({
            'id': subscription.id,
            'topic_id': subscription.topic_id,
            'user_id': subscription.user_id,
            'created_date': subscription.created_date.isoformat(),
            'notify_on_new_post': subscription.notify_on_new_post,
        })
    
    elif request.method == 'DELETE':
        subscription.delete()
        return JsonResponse({'message': 'TopicSubscription deleted successfully'}, status=200)


# ModeratorAction API
@csrf_exempt
@require_http_methods(["GET", "POST"])
def moderatoraction_list_create(request):
    if request.method == 'GET':
        actions = ModeratorAction.objects.all()
        data = []
        for action in actions:
            data.append({
                'id': action.id,
                'moderator_id': action.moderator_id,
                'action_type': action.action_type,
                'description': action.description,
                'target_type': action.target_type,
                'target_id': action.target_id,
                'created_date': action.created_date.isoformat(),
            })
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            moderator = None
            if data.get('moderator_id'):
                moderator = User.objects.get(id=data['moderator_id'])
            action = ModeratorAction.objects.create(
                moderator=moderator,
                action_type=data['action_type'],
                description=data['description'],
                target_type=data['target_type'],
                target_id=data['target_id'],
            )
            return JsonResponse({
                'id': action.id,
                'moderator_id': action.moderator_id,
                'action_type': action.action_type,
                'created_date': action.created_date.isoformat(),
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def moderatoraction_detail(request, moderatoraction_id):
    try:
        action = ModeratorAction.objects.get(id=moderatoraction_id)
    except ModeratorAction.DoesNotExist:
        return JsonResponse({'error': 'ModeratorAction not found'}, status=404)
    
    if request.method == 'GET':
        return JsonResponse({
            'id': action.id,
            'moderator_id': action.moderator_id,
            'action_type': action.action_type,
            'description': action.description,
            'target_type': action.target_type,
            'target_id': action.target_id,
            'created_date': action.created_date.isoformat(),
        })
    
    elif request.method == 'DELETE':
        action.delete()
        return JsonResponse({'message': 'ModeratorAction deleted successfully'}, status=200)


# AdminLog API
@csrf_exempt
@require_http_methods(["GET", "POST"])
def adminlog_list_create(request):
    if request.method == 'GET':
        logs = AdminLog.objects.all()
        data = []
        for log in logs:
            data.append({
                'id': log.id,
                'admin_id': log.admin_id,
                'action_type': log.action_type,
                'description': log.description,
                'affected_resource_type': log.affected_resource_type,
                'affected_resource_id': log.affected_resource_id,
                'created_date': log.created_date.isoformat(),
            })
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            admin = None
            if data.get('admin_id'):
                admin = User.objects.get(id=data['admin_id'])
            log = AdminLog.objects.create(
                admin=admin,
                action_type=data['action_type'],
                description=data['description'],
                affected_resource_type=data.get('affected_resource_type', ''),
                affected_resource_id=data.get('affected_resource_id'),
            )
            return JsonResponse({
                'id': log.id,
                'admin_id': log.admin_id,
                'action_type': log.action_type,
                'created_date': log.created_date.isoformat(),
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def adminlog_detail(request, adminlog_id):
    try:
        log = AdminLog.objects.get(id=adminlog_id)
    except AdminLog.DoesNotExist:
        return JsonResponse({'error': 'AdminLog not found'}, status=404)
    
    if request.method == 'GET':
        return JsonResponse({
            'id': log.id,
            'admin_id': log.admin_id,
            'action_type': log.action_type,
            'description': log.description,
            'affected_resource_type': log.affected_resource_type,
            'affected_resource_id': log.affected_resource_id,
            'created_date': log.created_date.isoformat(),
        })
    
    elif request.method == 'DELETE':
        log.delete()
        return JsonResponse({'message': 'AdminLog deleted successfully'}, status=200)


# Notification API
@csrf_exempt
@require_http_methods(["GET", "POST"])
def notification_list_create(request):
    if request.method == 'GET':
        notifications = Notification.objects.all()
        data = []
        for notification in notifications:
            data.append({
                'id': notification.id,
                'user_id': notification.user_id,
                'notification_type': notification.notification_type,
                'title': notification.title,
                'message': notification.message,
                'is_read': notification.is_read,
                'created_date': notification.created_date.isoformat(),
                'related_resource_type': notification.related_resource_type,
                'related_resource_id': notification.related_resource_id,
            })
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            user = User.objects.get(id=data['user_id'])
            notification = Notification.objects.create(
                user=user,
                notification_type=data['notification_type'],
                title=data['title'],
                message=data['message'],
                is_read=data.get('is_read', False),
                related_resource_type=data.get('related_resource_type', ''),
                related_resource_id=data.get('related_resource_id'),
            )
            return JsonResponse({
                'id': notification.id,
                'user_id': notification.user_id,
                'notification_type': notification.notification_type,
                'title': notification.title,
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def notification_detail(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id)
    except Notification.DoesNotExist:
        return JsonResponse({'error': 'Notification not found'}, status=404)
    
    if request.method == 'GET':
        return JsonResponse({
            'id': notification.id,
            'user_id': notification.user_id,
            'notification_type': notification.notification_type,
            'title': notification.title,
            'message': notification.message,
            'is_read': notification.is_read,
            'created_date': notification.created_date.isoformat(),
            'related_resource_type': notification.related_resource_type,
            'related_resource_id': notification.related_resource_id,
        })
    
    elif request.method == 'DELETE':
        notification.delete()
        return JsonResponse({'message': 'Notification deleted successfully'}, status=200)


# SearchIndex API
@csrf_exempt
@require_http_methods(["GET", "POST"])
def searchindex_list_create(request):
    if request.method == 'GET':
        indices = SearchIndex.objects.all()
        data = []
        for index in indices:
            data.append({
                'id': index.id,
                'content_type': index.content_type,
                'object_id': index.object_id,
                'search_vector': index.search_vector,
                'tags': index.tags,
                'author_username': index.author_username,
                'created_date': index.created_date.isoformat(),
                'last_updated': index.last_updated.isoformat(),
            })
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            from django.utils.dateparse import parse_datetime
            index = SearchIndex.objects.create(
                content_type=data['content_type'],
                object_id=data['object_id'],
                search_vector=data.get('search_vector', ''),
                tags=data.get('tags', ''),
                author_username=data.get('author_username', ''),
                created_date=parse_datetime(data['created_date']) if data.get('created_date') else None,
            )
            return JsonResponse({
                'id': index.id,
                'content_type': index.content_type,
                'object_id': index.object_id,
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def searchindex_detail(request, searchindex_id):
    try:
        index = SearchIndex.objects.get(id=searchindex_id)
    except SearchIndex.DoesNotExist:
        return JsonResponse({'error': 'SearchIndex not found'}, status=404)
    
    if request.method == 'GET':
        return JsonResponse({
            'id': index.id,
            'content_type': index.content_type,
            'object_id': index.object_id,
            'search_vector': index.search_vector,
            'tags': index.tags,
            'author_username': index.author_username,
            'created_date': index.created_date.isoformat(),
            'last_updated': index.last_updated.isoformat(),
        })
    
    elif request.method == 'DELETE':
        index.delete()
        return JsonResponse({'message': 'SearchIndex deleted successfully'}, status=200)


# GitHubAuth API
@csrf_exempt
@require_http_methods(["GET", "POST"])
def githubauth_list_create(request):
    if request.method == 'GET':
        auths = GitHubAuth.objects.all()
        data = []
        for auth in auths:
            data.append({
                'user_id': auth.user_id,
                'github_id': auth.github_id,
                'github_username': auth.github_username,
                'access_token': auth.access_token,
                'refresh_token': auth.refresh_token,
                'created_date': auth.created_date.isoformat(),
                'last_sync': auth.last_sync.isoformat(),
            })
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            user = User.objects.get(id=data['user_id'])
            auth = GitHubAuth.objects.create(
                user=user,
                github_id=data['github_id'],
                github_username=data['github_username'],
                access_token=data['access_token'],
                refresh_token=data.get('refresh_token', ''),
            )
            return JsonResponse({
                'user_id': auth.user_id,
                'github_id': auth.github_id,
                'github_username': auth.github_username,
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def githubauth_detail(request, user_id):
    try:
        auth = GitHubAuth.objects.get(user_id=user_id)
    except GitHubAuth.DoesNotExist:
        return JsonResponse({'error': 'GitHubAuth not found'}, status=404)
    
    if request.method == 'GET':
        return JsonResponse({
            'user_id': auth.user_id,
            'github_id': auth.github_id,
            'github_username': auth.github_username,
            'access_token': auth.access_token,
            'refresh_token': auth.refresh_token,
            'created_date': auth.created_date.isoformat(),
            'last_sync': auth.last_sync.isoformat(),
        })
    
    elif request.method == 'DELETE':
        auth.delete()
        return JsonResponse({'message': 'GitHubAuth deleted successfully'}, status=200)


# TopicView API
@csrf_exempt
@require_http_methods(["GET", "POST"])
def topicview_list_create(request):
    if request.method == 'GET':
        views = TopicView.objects.all()
        data = []
        for view in views:
            data.append({
                'id': view.id,
                'topic_id': view.topic_id,
                'user_id': view.user_id,
                'view_date': view.view_date.isoformat(),
            })
        return JsonResponse(data, safe=False)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            topic = Topic.objects.get(id=data['topic_id'])
            user = User.objects.get(id=data['user_id'])
            view, created = TopicView.objects.get_or_create(
                topic=topic,
                user=user,
            )
            return JsonResponse({
                'id': view.id,
                'topic_id': view.topic_id,
                'user_id': view.user_id,
                'view_date': view.view_date.isoformat(),
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def topicview_detail(request, topicview_id):
    try:
        view = TopicView.objects.get(id=topicview_id)
    except TopicView.DoesNotExist:
        return JsonResponse({'error': 'TopicView not found'}, status=404)
    
    if request.method == 'GET':
        return JsonResponse({
            'id': view.id,
            'topic_id': view.topic_id,
            'user_id': view.user_id,
            'view_date': view.view_date.isoformat(),
        })
    
    elif request.method == 'DELETE':
        view.delete()
        return JsonResponse({'message': 'TopicView deleted successfully'}, status=200)

