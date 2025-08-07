from django.db import models
from django.contrib.auth.models import User
from problem_detail.models import Question
# Create your models here.

class CodeSubmission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True, blank=True)
    language = models.CharField(max_length=100)
    code = models.TextField()
    input_data = models.TextField(null=True,blank=True)
    output_data = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    verdict = models.CharField(max_length=50, blank=True, null=True) # e.g., "Accepted", "Wrong Answer"
    score = models.FloatField(default=0.0)
    submitted_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)

    def __str__(self):
        return f"Submission by {self.user.username} for {self.question.title} in {self.language}"