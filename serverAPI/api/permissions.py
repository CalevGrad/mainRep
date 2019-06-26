from rest_framework import permissions
from api.models import DialogOwners

class MessagePermissions(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        if request.method in ['PATCH', 'PUT']:
            if 'date' in request.data.keys():
                return False

        if obj.owner == request.user:
            return True

        if len(DialogOwners.objects.filter(owner=request.user, dialog=obj.ownerDialog)) != 0:
            return True

        return False


class DialogPermissions(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        if request.method in permissions.SAFE_METHODS and (len(DialogOwners.objects.filter(owner=request.user, dialog=obj)) != 0): #выдать диалоги, если методы запроса и клиент состоит в диалоге
            return True
        
        return False


class UserPermissions(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        if request.method in ['PATCH', 'PUT'] and request and request.user == obj:
            return True
        
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return False


class DialogOwnersPermissions(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        if request.method == permissions.SAFE_METHODS and request.user == obj.owner:
            return True

        return False