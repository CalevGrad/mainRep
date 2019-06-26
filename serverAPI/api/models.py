from django.db import models

class Dialog(models.Model):
    textLastMessage = models.TextField(default="")
    dateLastMessage = models.DateTimeField(auto_now_add=True)
    idLastMessage = models.IntegerField(default=0)

class DialogOwners(models.Model):
    owner = models.ForeignKey('auth.User', related_name='dialogsID', on_delete=models.CASCADE)
    dialog = models.ForeignKey(Dialog, related_name='owners', on_delete=models.CASCADE)

class Message(models.Model):
    ownerDialog = models.ForeignKey(Dialog, related_name='messages', on_delete=models.CASCADE)
    owner = models.ForeignKey('auth.User', related_name='messages', on_delete=models.CASCADE)
    text = models.TextField()
    date = models.DateTimeField()
