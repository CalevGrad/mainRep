from rest_framework import serializers
from api.models import Message, Dialog, DialogOwners
from django.contrib.auth.models import User

class MessageSerializer(serializers.HyperlinkedModelSerializer):
    ownerID = serializers.ReadOnlyField(source='owner.id')
    dialogID = serializers.ReadOnlyField(source='ownerDialog.id')

    class Meta:
        model = Message
        fields = ('url', 'id', 'text', 'ownerID', 'dialogID', 'date')


class OwnersListingField(serializers.RelatedField):
    def to_representation(self, value):
        return {value.owner.username : value.owner.id}

class DialogSerializer(serializers.HyperlinkedModelSerializer):
    #messages = serializers.HyperlinkedRelatedField(many=True, view_name='message-detail', read_only=True)
    owners = OwnersListingField(many=True, read_only=True)

    class Meta:
        model = Dialog
        fields = ('url', 'id', 'owners', 'textLastMessage', 'dateLastMessage', 'idLastMessage')#, 'messages')


class DialogOwnersSerializer(serializers.HyperlinkedModelSerializer):
    ownerID = serializers.ReadOnlyField(source='owner.id')
    dialog = serializers.ReadOnlyField(source='dialog.id')

    class Meta:
        model = DialogOwners
        fields = ('url', 'id', 'ownerID', 'dialog')


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'id', 'username')
    