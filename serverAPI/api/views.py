from api.serializers import UserSerializer, DialogSerializer, MessageSerializer, DialogOwnersSerializer
from api.permissions import MessagePermissions, DialogPermissions, UserPermissions, DialogOwnersPermissions
from rest_framework import viewsets, permissions
from django.contrib.auth.models import User
from api.models import Message, Dialog, DialogOwners
from rest_framework import status
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime
from rest_framework.decorators import action

import time

class UserViewSet(viewsets.ModelViewSet):
    """
    'list' and 'detail' actions for Users
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.AllowAny, UserPermissions)

    @action(detail=True)
    def longpolling(self, request, *args, **kwargs):
        if request.user != User.objects.get(id=kwargs['pk']):
            return Response(status=status.HTTP_403_FORBIDDEN)

        data = str()    #пустые данные, т.к. нету диалогов у клиента?
        data = request.GET.get("data")

        if data == None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        arr = data.split()

        processedData = [ [0] * 2 for i in range( len(arr) // 2 ) ]

        for i in range(0, len(arr), 2):
            processedData[ i // 2 ][0] = int(arr[i])
            processedData[ i // 2 ][1] = int(arr[i + 1])

        querysetDialog = list() #диалоги пользователя
        Dialogs_Message = dict()
        queryset = list() #отправляемые данные

        for item in DialogOwners.objects.filter(owner=request.user):
            querysetDialog.append(item.dialog)

        for i in range( len(processedData) ):
            if Dialog.objects.filter( id=int(processedData[i][0]) ) != 0: #если диалог существует
                dialog = Dialog.objects.get( id=int(processedData[i][0]) )
                if dialog in querysetDialog: #если диалог принадлежит клиенту
                    Dialogs_Message[dialog] = int(processedData[i][1])
        
        chck = True #флаг
        keys = Dialogs_Message.keys() #ключи словаря
        start_time = time.time()

        while (chck):
            querysetDialog.clear()
            time.sleep(0.1)
            if time.time() - start_time > 10:
                chck = False

            if len(DialogOwners.objects.filter(owner=request.user)) != len(Dialogs_Message): #если количество диалогов не совпадает
                chck = False
                for item in DialogOwners.objects.filter(owner=request.user):
                    querysetDialog.append(item.dialog)
                for i in range( len(querysetDialog) ):
                    if querysetDialog[i] not in keys:
                        queryset.append(querysetDialog[i])

            for key in keys:
                if Dialogs_Message[key] != Dialog.objects.get(id=key.id).idLastMessage:
                    queryset.append(key)
                    chck = False

        page = self.paginate_queryset(queryset)
        kwrg = dict()
        kwrg['many'] = True
        kwrg['context'] = {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        } 

        if page is not None:
            serializer = DialogSerializer(page, **kwrg)
            return self.get_paginated_response(serializer.data)
        
        serializer = DialogSerializer(queryset, **kwrg)
        return Response(serializer.data)

    @action(detail=False)
    def search(self, request, *args, **kwargs):
        """
        parameters: 'username'
        """
        username = request.GET.get("username")

        if username == None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        queryset = list() 
        for item in User.objects.all():
            if username in item.username:
                queryset.append(item)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def check(self, request, *args, **kwargs):
        if request.user.is_anonymous:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)
        if request.user in User.objects.all():
            queryset = list()
            queryset.append(request.user)

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        parameters POST: 'username', 'password'
        """
        for parameter in ['username', 'password']:
            if parameter not in request.data:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        
        allowedSymbols = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"

        if len(request.data['password']) < 4 or len(request.data['username']) < 4 or len(request.data['password']) > 20 or len(request.data['username']) > 20:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        for i in range(len(request.data['password'])):
            if request.data['password'][i] not in allowedSymbols:
                return Response(status=status.HTTP_400_BAD_REQUEST)

        for i in range(len(request.data['username'])):
            if request.data['username'][i] not in allowedSymbols:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        
        if len( User.objects.filter(username=request.data['username']) ) != 0:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(request.data['username'], '', request.data['password'])
        queryset = list()
        queryset.append(user)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)



def sortMessage(inputData):
    return inputData.date

class MessageViewSet(viewsets.ModelViewSet):
    """
    All actions for Message
    """
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = (permissions.IsAuthenticated, MessagePermissions)
    

    def list(self, request, *args, **kwargs):
        querysetDialogOwners = DialogOwners.objects.filter(owner=request.user)
        querysetDialog = list()
        queryset = list()

        for item in querysetDialogOwners:
            querysetDialog.append(item.dialog)
        for item in querysetDialog:
            for item2 in Message.objects.filter(ownerDialog=item):
                queryset.append(item2)

        queryset.sort(key=sortMessage, reverse=True)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


    def create(self, request, *args, **kwargs):
        """
        parameters POST: 'dialogID', 'text'
        """
        for parameter in ['dialogID', 'text']:
            if parameter not in request.data:
                return Response(status=status.HTTP_400_BAD_REQUEST)

        dialog = Dialog.objects.get(pk=request.data['dialogID'])
        message = Message()
        message.owner = request.user
        message.ownerDialog = dialog
        message.text = request.data['text']
        message.date = timezone.now()
        message.save()

        if dialog.dateLastMessage < message.date:
            dialog.dateLastMessage = message.date
            dialog.textLastMessage = message.text
            dialog.idLastMessage = message.id
            dialog.save()

        #data = [{ 'id':message.id }, { 'date':message.date }]
        return Response(status=status.HTTP_201_CREATED)


def sortDialog(inputData):
    if len(Message.objects.filter(ownerDialog=inputData).order_by('-date')):
        return Message.objects.filter(ownerDialog=inputData).order_by('-date')[0].date
    else: 
        return datetime(1, 1, 1, 0, 0, 0, 0)
        
class DialogViewSet(viewsets.ModelViewSet):
    """
    'create', 'list' and 'detail' actions for Dialog
    """
    queryset = Dialog.objects.all()
    serializer_class = DialogSerializer
    permission_classes = (permissions.IsAuthenticated, DialogPermissions)

    """
    @action(detail=True)
    def lastmessage(self, request, *args, **kwargs):
        if len(DialogOwners.objects.filter(owner=request.user, dialog=Dialog.objects.get( id=kwargs['pk']))) == 0:
            return Response({}, status=status.HTTP_403_FORBIDDEN)

        queryset = list()
        DialogViewSet.serializer_class = MessageSerializer

        for item in Message.objects.filter( ownerDialog=Dialog.objects.get( id=kwargs['pk']) ).order_by('-date'):
            queryset.append(item)
            break

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            DialogViewSet.serializer_class = DialogSerializer
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        DialogViewSet.serializer_class = DialogSerializer
        return Response(serializer.data)
    """

    @action(detail=True)
    def messages(self, request, *args, **kwargs):
        """
        parameters: 'messageID', 'countMessages', 'indent'
        """
        messageID = request.GET.get("messageID")
        countMessages = request.GET.get("countMessages")
        indent = request.GET.get("indent", 0)
        for parameter in [messageID, countMessages, indent]:
            if parameter == None:
                return Response(status=status.HTTP_400_BAD_REQUEST)

        dialog = Dialog.objects.get(id=kwargs['pk'])

        if len( Message.objects.filter(ownerDialog=dialog, id=messageID) ) == 0:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if len( DialogOwners.objects.filter(owner=request.user, dialog=Dialog.objects.get( id=kwargs['pk'])) ) == 0:
            return Response(status=status.HTTP_403_FORBIDDEN)
        
        queryset = list()
        message = Message.objects.get(ownerDialog=dialog, id=messageID)
        i = int( countMessages )
        indent = int( indent )
        check = False

        for item in Message.objects.filter(ownerDialog=dialog).order_by('-id'):
            if i == 0:
                break
            if item == message:
                check = True
            if check and indent != 0:
                indent -= 1
                continue
            if check:
                i -= 1
                queryset.append(item)

        page = self.paginate_queryset(queryset)
        kwrg = dict()
        kwrg['many'] = True
        kwrg['context'] = {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        } 

        if page is not None:
            serializer = MessageSerializer(page, **kwrg)
            return self.get_paginated_response(serializer.data)
        
        serializer = MessageSerializer(queryset, **kwrg)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        queryset = list()
        for item in DialogOwners.objects.filter(owner=request.user):
            queryset.append(item.dialog)

        queryset.sort(key=sortDialog, reverse=True)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        parameters: 'recipientID', 'textFirstMessage'
        """
        for parameter in ['recipientID', 'textFirstMessage']:
            if parameter not in request.data:
                print(3333)
                return Response(status=status.HTTP_400_BAD_REQUEST)

        recipientID = request.data['recipientID']
        textFirstMessage = request.data['textFirstMessage']

        querysetDialogsUser = list()
        querysetDialogsRecipient = list()

        #exist dialog?
        for item in DialogOwners.objects.filter(owner=request.user):
            querysetDialogsUser.append(item.dialog)
        for item in DialogOwners.objects.filter(owner=User.objects.get(id=recipientID)):
            querysetDialogsRecipient.append(item.dialog)
        
        #if dialog exist
        for item in querysetDialogsUser:
            if querysetDialogsRecipient.count(item) != 0:
                return Response(status=status.HTTP_400_BAD_REQUEST)

        dialog = Dialog()
        dialog.save()

        message = Message()
        message.owner = request.user
        message.ownerDialog = dialog
        message.text = textFirstMessage
        message.date = timezone.now()
        message.save()

        dialog.textLastMessage = textFirstMessage
        dialog.dateLastMessage = message.date
        dialog.idLastMessage = message.id

        dialog.save()

        dialogOwner1 = DialogOwners()
        dialogOwner2 = DialogOwners()

        dialogOwner1.owner = request.user
        dialogOwner1.dialog = dialog
        dialogOwner2.owner = User.objects.get(id=recipientID)
        dialogOwner2.dialog = dialog

        dialogOwner1.save()
        dialogOwner2.save()

        #data = [{ 'id':dialog.id }]
        return Response(status=status.HTTP_201_CREATED)

class DialogOwnersViewSet(viewsets.ModelViewSet):
    queryset = DialogOwners.objects.all()
    serializer_class = DialogOwnersSerializer
    permission_classes = (permissions.IsAuthenticated, DialogOwnersPermissions)

    def list(self, request, *args, **kwargs):
        queryset = DialogOwners.objects.filter(owner=request.user)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
