from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class BankAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='bank_account')
    account_holder_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=20, unique=True)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.account_holder_name} - {self.account_number}"

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAWAL', 'Withdrawal'),
    )
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    timestamp = models.DateTimeField(default=timezone.now)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ['-timestamp']  # newest first

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} on {self.timestamp}"