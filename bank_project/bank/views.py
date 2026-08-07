from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.core.paginator import Paginator
from django.http import HttpResponse
import csv

from .utils import generate_account_number
from .models import BankAccount, Transaction
from .forms import RegistrationForm, DepositForm, WithdrawForm, TransactionFilterForm

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create bank account
            BankAccount.objects.create(
                user=user,
                account_holder_name=form.cleaned_data['account_holder_name'],
                account_number=form.cleaned_data['account_number'],
                current_balance=0.00
            )
            login(request, user)
            messages.success(request, "Registration successful.")
            return redirect('dashboard')
    else:
        form = RegistrationForm()
    return render(request, 'bank/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid credentials.")
    return render(request, 'bank/login.html')


def user_logout(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    account, created = BankAccount.objects.get_or_create(
        user=request.user,
        defaults={
            'account_holder_name': request.user.username,
            'account_number': generate_account_number(),
            'current_balance': 0.00
        }
    )
    if created:
        # optional message
        pass

    transactions = account.transactions.all()
    total_deposits = transactions.filter(transaction_type='DEPOSIT').aggregate(Sum('amount'))['amount__sum'] or 0
    total_withdrawals = transactions.filter(transaction_type='WITHDRAWAL').aggregate(Sum('amount'))['amount__sum'] or 0
    total_transactions = transactions.count()

    context = {
        'account': account,
        'total_deposits': total_deposits,
        'total_withdrawals': total_withdrawals,
        'total_transactions': total_transactions,
    }
    return render(request, 'bank/dashboard.html', context)

@login_required
def deposit(request):
    account, created  = BankAccount.objects.get_or_create(
        user=request.user,
        defaults={
            'account_holder_name': request.user.get_full_name() or request.user.username,
            'account_number': generate_account_number(),
            'current_balance': 0.00
        }
    )
    if request.method == 'POST':
        form = DepositForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            account.current_balance += amount
            account.save()
            Transaction.objects.create(
                account=account,
                transaction_type='DEPOSIT',
                amount=amount,
                balance_after=account.current_balance
            )
            messages.success(request, f"Deposited ₹{amount} successfully.")
            return redirect('dashboard')
    else:
        form = DepositForm()
    return render(request, 'bank/deposit.html', {'form': form})

@login_required
def withdraw(request):
    account, created  = BankAccount.objects.get_or_create(
        user=request.user,
        defaults={
            'account_holder_name': request.user.get_full_name() or request.user.username,
            'account_number': generate_account_number(),
            'current_balance': 0.00
        }
    )
    if request.method == 'POST':
        form = WithdrawForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            if amount > account.current_balance:
                messages.error(request, "Insufficient balance. Withdrawal denied.")
            else:
                account.current_balance -= amount
                account.save()
                Transaction.objects.create(
                    account=account,
                    transaction_type='WITHDRAWAL',
                    amount=amount,
                    balance_after=account.current_balance
                )
                messages.success(request, f"Withdrew ₹{amount} successfully.")
            return redirect('dashboard')
    else:
        form = WithdrawForm()
    return render(request, 'bank/withdraw.html', {'form': form})

@login_required
def transaction_history(request):
    account, created  = BankAccount.objects.get_or_create(
        user=request.user,
        defaults={
            'account_holder_name': request.user.get_full_name() or request.user.username,
            'account_number': generate_account_number(),
            'current_balance': 0.00
        }
    )
    transactions = account.transactions.all()
    filter_form = TransactionFilterForm(request.GET or None)
    
    if filter_form.is_valid():
        t_type = filter_form.cleaned_data.get('transaction_type')
        start = filter_form.cleaned_data.get('start_date')
        end = filter_form.cleaned_data.get('end_date')
        if t_type:
            transactions = transactions.filter(transaction_type=t_type)
        if start:
            transactions = transactions.filter(timestamp__date__gte=start)
        if end:
            transactions = transactions.filter(timestamp__date__lte=end)
    
    # Pagination (Bonus)
    paginator = Paginator(transactions, 10)  # 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'bank/transaction_history.html', {
        'page_obj': page_obj,
        'filter_form': filter_form,
    })

@login_required
def export_csv(request):
    account, created = BankAccount.objects.get_or_create(
        user=request.user,
        defaults={
            'account_holder_name': request.user.get_full_name() or request.user.username,
            'account_number': generate_account_number(),
            'current_balance': 0.00
        }
    )
    transactions = account.transactions.all()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
    writer = csv.writer(response)
    writer.writerow(['Type', 'Amount', 'Date', 'Balance After'])
    for t in transactions:
        writer.writerow([t.transaction_type, t.amount, t.timestamp, t.balance_after])
    return response