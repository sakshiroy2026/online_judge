from django.db import models
from django.contrib.auth.models import User
from dashboard.models import Question,Topic

class TestCase(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE,related_name='name',null=True,blank=True)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE,related_name='topic',null=True,blank=True)
    difficulty = models.CharField(max_length=10, choices=[("Easy", "Easy"), ("Med.", "Medium"), ("Hard", "Hard")],null=True,blank=True)
    description=models.TextField(null=True,blank=True)
    

    # --- Visible Test Case Files (for 'Run') ---
    input_file = models.FileField(upload_to='testcases/inputs/', help_text="File with visible test cases, separated by '---'")
    output_file = models.FileField(upload_to='testcases/outputs/', help_text="File with corresponding visible outputs")
    
    # --- NEW: Hidden Test Case Files (for 'Submit') ---
    hidden_input_file = models.FileField(upload_to='testcases/hidden_inputs/', blank=True, null=True, help_text="Optional: File with hidden test cases")
    hidden_output_file = models.FileField(upload_to='testcases/hidden_outputs/', blank=True, null=True, help_text="Optional: Corresponding hidden outputs")

    is_visible = models.BooleanField(default=True) # This can now represent the visibility of the sample cases

    constraints=models.TextField(null=True,blank=True)
    explanations=models.TextField(null=True,blank=True)
    


