from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import BankAccount, Transaction

class RegistrationForm(UserCreationForm):
    account_holder_name = forms.CharField(max_length=100)
    account_number = forms.CharField(max_length=20)

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'account_holder_name', 'account_number']

    def clean_account_number(self):
        acc = self.cleaned_data['account_number']
        if BankAccount.objects.filter(account_number=acc).exists():
            raise forms.ValidationError("Account number already exists.")
        return acc

class DepositForm(forms.Form):
    amount = forms.DecimalField(min_value=0.01, max_digits=12, decimal_places=2)

class WithdrawForm(forms.Form):
    amount = forms.DecimalField(min_value=0.01, max_digits=12, decimal_places=2)

class TransactionFilterForm(forms.Form):
    transaction_type = forms.ChoiceField(choices=[('', 'All')] + list(Transaction.TRANSACTION_TYPES), required=False)
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))