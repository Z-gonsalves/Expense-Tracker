import tkinter as tk 
from tkinter import messagebox
from tkinter import ttk 
import json
from datetime import datetime
import os
from collections import defaultdict
import requests
from decimal import Decimal
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Define new color scheme
COLORS = {
    'primary': '#78999E',      # Main teal color
    'secondary': '#536F80',    # Dark blue-gray
    'accent': '#B0C6C5',       # Light teal
    'background': '#FFFFFF',   # White
    'text': '#2D3436',         # Dark gray
    'success': '#8FA1B5',      # Muted blue
    'danger': '#FF7675',       # Coral red
    'warning': '#FDCB6E',      # Yellow
    'white': '#FFFFFF',
    'hover': '#8FA1B5',        # Hover color for buttons
    'card_bg': '#F5F6FA',      # Light gray
    'border': '#DFE6E9'        # Light border
}

class Transaction:
    def __init__(self, transaction_type, amount, description, category, currency="INR", date=None):
        self.transaction_type = transaction_type
        self.amount = amount
        self.description = description
        self.category = category
        self.currency = currency
        self.date = date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class ExpensesIncomesTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Expense Tracker")
        self.root.geometry("1000x800")
        self.root.configure(bg=COLORS['background'])

        # Configure style
        self.style = ttk.Style()
        self.style.configure('TFrame', background=COLORS['background'])
        self.style.configure('TLabel', background=COLORS['background'], foreground=COLORS['text'])
        self.style.configure('TButton', padding=5)
        self.style.configure('TNotebook', background=COLORS['background'])
        self.style.configure('TNotebook.Tab', padding=[15, 5], background=COLORS['card_bg'])
        self.style.configure('Treeview', background=COLORS['white'], fieldbackground=COLORS['white'])
        self.style.configure('Treeview.Heading', background=COLORS['primary'], foreground=COLORS['white'])
        self.style.configure('TEntry', fieldbackground=COLORS['white'])
        self.style.configure('TCombobox', fieldbackground=COLORS['white'])
        self.style.configure('Card.TFrame', background=COLORS['card_bg'])

        # Initialize variables
        self.transaction_var = tk.StringVar()
        self.total_incomes = tk.DoubleVar()
        self.total_expenses = tk.DoubleVar()
        self.total_balance = tk.DoubleVar()
        self.description = tk.StringVar()
        self.transactions = []
        self.categories = ["Food", "Transport", "Bills", "Entertainment", "Shopping", "Other"]
        self.category_var = tk.StringVar(value="Other")
        self.search_var = tk.StringVar()
        self.filter_type_var = tk.StringVar(value="All")
        self.filter_category_var = tk.StringVar(value="All")
        
        # Currency settings
        self.currencies = ["INR", "USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY"]
        self.default_currency = tk.StringVar(value="INR")
        self.currency_rates = {}
        self.load_currency_rates()

        # Create main container
        self.main_container = ttk.Frame(root)
        self.main_container.pack(expand=True, fill='both', padx=20, pady=20)

        # Create header
        self.create_header()

        # Create the main notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(expand=True, fill='both', pady=10)

        # Create frames for each tab
        self.transactions_frame = ttk.Frame(self.notebook)
        self.converter_frame = ttk.Frame(self.notebook)
        self.settings_frame = ttk.Frame(self.notebook)
        self.visualization_frame = ttk.Frame(self.notebook)  # New visualization tab

        # Add tabs to notebook
        self.notebook.add(self.transactions_frame, text='Transactions')
        self.notebook.add(self.converter_frame, text='Currency Converter')
        self.notebook.add(self.settings_frame, text='Settings')
        self.notebook.add(self.visualization_frame, text='Visualization')  # Add visualization tab

        # Create content for each tab
        self.create_transactions_tab()
        self.create_converter_tab()
        self.create_settings_tab()
        self.create_visualization_tab()  # Create visualization tab content

        # Load saved transactions
        self.load_transactions()

    def create_header(self):
        header_frame = ttk.Frame(self.main_container, style='Card.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 20))

        # App title
        title_label = tk.Label(header_frame, text=" MY-Tracker", 
        font=("Helvetica", 28, "bold"), bg=COLORS['card_bg'], fg=COLORS['primary'])
        title_label.pack(side=tk.LEFT, padx=20, pady=10)

        # Summary cards
        summary_frame = ttk.Frame(header_frame)
        summary_frame.pack(side=tk.RIGHT, padx=20, pady=10)

        # Balance card
        balance_card = ttk.Frame(summary_frame, style='Card.TFrame')
        balance_card.pack(side=tk.LEFT, padx=5)
        tk.Label(balance_card, text="Balance", font=("Helvetica", 12), 
        bg=COLORS['card_bg'], fg=COLORS['text']).pack()
        self.total_balance_display = tk.Label(balance_card, 
        textvariable=self.total_balance, font=("Helvetica", 16, "bold"), 
        bg=COLORS['card_bg'], fg=COLORS['primary'])
        self.total_balance_display.pack()

        # Income card
        income_card = ttk.Frame(summary_frame, style='Card.TFrame')
        income_card.pack(side=tk.LEFT, padx=5)
        tk.Label(income_card, text="Income", font=("Helvetica", 12), 
        bg=COLORS['card_bg'], fg=COLORS['text']).pack()
        self.total_incomes_display = tk.Label(income_card, 
        textvariable=self.total_incomes, font=("Helvetica", 16, "bold"), 
        bg=COLORS['card_bg'], fg=COLORS['success'])
        self.total_incomes_display.pack()

        # Expense card
        expense_card = ttk.Frame(summary_frame, style='Card.TFrame')
        expense_card.pack(side=tk.LEFT, padx=5)
        tk.Label(expense_card, text="Expenses", font=("Helvetica", 12), 
        bg=COLORS['card_bg'], fg=COLORS['text']).pack()
        self.total_expenses_display = tk.Label(expense_card, 
        textvariable=self.total_expenses, font=("Helvetica", 16, "bold"), 
        bg=COLORS['card_bg'], fg=COLORS['danger'])
        self.total_expenses_display.pack()

    def create_transactions_tab(self):
        # Left panel for adding transactions
        left_panel = ttk.Frame(self.transactions_frame, style='Card.TFrame')
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        # Transaction type selection
        type_frame = ttk.LabelFrame(left_panel, text="Transaction Type", padding=10)
        type_frame.pack(fill=tk.X, padx=10, pady=5)
        
        expenseRadio = ttk.Radiobutton(type_frame, text="Expense", 
        variable=self.transaction_var, value="Expense")
        incomeRadio = ttk.Radiobutton(type_frame, text="Income", 
        variable=self.transaction_var, value="Income")
        expenseRadio.pack(side=tk.LEFT, padx=10)
        incomeRadio.pack(side=tk.LEFT, padx=10)

        # New transaction form
        form_frame = ttk.LabelFrame(left_panel, text="New Transaction", padding=10)
        form_frame.pack(fill=tk.X, padx=10, pady=5)

        # Amount entry
        ttk.Label(form_frame, text="Amount").pack(anchor=tk.W)
        self.amountEntry = ttk.Entry(form_frame, width=30)
        self.amountEntry.pack(fill=tk.X, pady=2)

        # Category selection
        ttk.Label(form_frame, text="Category").pack(anchor=tk.W)
        category_combo = ttk.Combobox(form_frame, textvariable=self.category_var, 
        values=self.categories, state="readonly", width=27)
        category_combo.pack(fill=tk.X, pady=2)

        # Description entry
        ttk.Label(form_frame, text="Description").pack(anchor=tk.W)
        self.descriptionEntry = ttk.Entry(form_frame, width=30)
        self.descriptionEntry.pack(fill=tk.X, pady=2)

        # Add Transaction button
        addButton = tk.Button(form_frame, text="Add Transaction", 
        bg=COLORS['primary'], fg=COLORS['white'], font=("Helvetica", 10, "bold"), 
        command=self.add_transaction, relief="flat", padx=10, pady=5)
        addButton.pack(fill=tk.X, pady=10)
        addButton.bind('<Enter>', lambda e: addButton.configure(bg=COLORS['hover']))
        addButton.bind('<Leave>', lambda e: addButton.configure(bg=COLORS['primary']))

        # Right panel for transaction list and filters
        right_panel = ttk.Frame(self.transactions_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Search and filter frame
        filter_frame = ttk.LabelFrame(right_panel, text="Search & Filter", padding=10)
        filter_frame.pack(fill=tk.X, pady=5)

        # Search
        search_frame = ttk.Frame(filter_frame)
        search_frame.pack(fill=tk.X, pady=2)
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        search_entry.bind('<KeyRelease>', lambda e: self.apply_filters())

        # Filters
        filter_buttons_frame = ttk.Frame(filter_frame)
        filter_buttons_frame.pack(fill=tk.X, pady=2)
        
        # Type filter
        ttk.Label(filter_buttons_frame, text="Type:").pack(side=tk.LEFT)
        type_filter = ttk.Combobox(filter_buttons_frame, textvariable=self.filter_type_var,
        values=["All", "Expense", "Income"], state="readonly", width=10)
        type_filter.pack(side=tk.LEFT, padx=5)
        type_filter.bind('<<ComboboxSelected>>', lambda e: self.apply_filters())

        # Category filter
        ttk.Label(filter_buttons_frame, text="Category:").pack(side=tk.LEFT, padx=(10,0))
        category_filter = ttk.Combobox(filter_buttons_frame, textvariable=self.filter_category_var,
        values=["All"] + self.categories, state="readonly", width=10)
        category_filter.pack(side=tk.LEFT, padx=5)
        category_filter.bind('<<ComboboxSelected>>', lambda e: self.apply_filters())

        # Transaction list
        list_frame = ttk.LabelFrame(right_panel, text="Transactions", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Create Treeview
        self.expenses_incomes_list = ttk.Treeview(list_frame, 
        columns=("Date", "Type", "Amount", "Currency", "Category", "Description"), 
        show="headings", height=15)

        # Configure columns
        self.expenses_incomes_list.heading("Date", text="Date")
        self.expenses_incomes_list.heading("Type", text="Type")
        self.expenses_incomes_list.heading("Amount", text="Amount")
        self.expenses_incomes_list.heading("Currency", text="Currency")
        self.expenses_incomes_list.heading("Category", text="Category")
        self.expenses_incomes_list.heading("Description", text="Description")
        
        self.expenses_incomes_list.column("Date", width=150)
        self.expenses_incomes_list.column("Type", width=100)
        self.expenses_incomes_list.column("Amount", width=100)
        self.expenses_incomes_list.column("Currency", width=70)
        self.expenses_incomes_list.column("Category", width=100)
        self.expenses_incomes_list.column("Description", width=200)
        
        self.expenses_incomes_list.pack(side="right", fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", 
        command=self.expenses_incomes_list.yview)
        scrollbar.pack(side="left", fill="y")
        self.expenses_incomes_list.config(yscrollcommand=scrollbar.set)

        # Action buttons
        buttons_frame = ttk.Frame(right_panel)
        buttons_frame.pack(fill=tk.X, pady=5)

        delete_button = tk.Button(buttons_frame, text="Delete Selected", 
        bg=COLORS['danger'], fg=COLORS['white'], font=("Helvetica", 10, "bold"), 
        command=self.delete_transaction, relief="flat", padx=10, pady=5)
        delete_button.pack(side=tk.LEFT, padx=5)
        delete_button.bind('<Enter>', lambda e: delete_button.configure(bg=COLORS['hover']))
        delete_button.bind('<Leave>', lambda e: delete_button.configure(bg=COLORS['danger']))

        edit_button = tk.Button(buttons_frame, text="Edit Selected", 
        bg=COLORS['secondary'], fg=COLORS['white'], font=("Helvetica", 10, "bold"), 
        command=self.edit_transaction, relief="flat", padx=10, pady=5)
        edit_button.pack(side=tk.LEFT, padx=5)
        edit_button.bind('<Enter>', lambda e: edit_button.configure(bg=COLORS['hover']))
        edit_button.bind('<Leave>', lambda e: edit_button.configure(bg=COLORS['secondary']))

        clear_button = tk.Button(buttons_frame, text="Clear All", 
        bg=COLORS['accent'], fg=COLORS['text'], font=("Helvetica", 10, "bold"), 
        command=self.clear_all_transactions, relief="flat", padx=10, pady=5)
        clear_button.pack(side=tk.LEFT, padx=5)
        clear_button.bind('<Enter>', lambda e: clear_button.configure(bg=COLORS['hover']))
        clear_button.bind('<Leave>', lambda e: clear_button.configure(bg=COLORS['accent']))

    def create_converter_tab(self):
        # Main container
        main_frame = ttk.Frame(self.converter_frame, style='Card.TFrame')
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)

        # Title
        title_label = tk.Label(main_frame, text="Currency Converter", 
        font=("Helvetica", 24, "bold"), bg=COLORS['card_bg'], fg=COLORS['primary'])
        title_label.pack(pady=20)

        # Converter form
        form_frame = ttk.LabelFrame(main_frame, text="Convert Currency", padding=20)
        form_frame.pack(pady=20)

        # Amount entry
        amount_frame = ttk.Frame(form_frame)
        amount_frame.pack(pady=10)
        ttk.Label(amount_frame, text="Amount:", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=5)
        self.convert_amount = ttk.Entry(amount_frame, width=15, font=("Helvetica", 12))
        self.convert_amount.pack(side=tk.LEFT, padx=5)

        # From currency
        from_frame = ttk.Frame(form_frame)
        from_frame.pack(pady=10)
        ttk.Label(from_frame, text="From:", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=5)
        self.from_currency = ttk.Combobox(from_frame, values=self.currencies, 
        state="readonly", width=10, font=("Helvetica", 12))
        self.from_currency.set("INR")
        self.from_currency.pack(side=tk.LEFT, padx=5)

        # To currency
        to_frame = ttk.Frame(form_frame)
        to_frame.pack(pady=10)
        ttk.Label(to_frame, text="To:", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=5)
        self.to_currency = ttk.Combobox(to_frame, values=self.currencies, 
        state="readonly", width=10, font=("Helvetica", 12))
        self.to_currency.set("USD")
        self.to_currency.pack(side=tk.LEFT, padx=5)

        # Convert button
        convert_btn = tk.Button(form_frame, text="Convert", 
        bg=COLORS['primary'], fg=COLORS['white'], font=("Helvetica", 12, "bold"), 
        command=self.convert_currency, relief="flat", padx=20, pady=10)
        convert_btn.pack(pady=20)
        convert_btn.bind('<Enter>', lambda e: convert_btn.configure(bg=COLORS['hover']))
        convert_btn.bind('<Leave>', lambda e: convert_btn.configure(bg=COLORS['primary']))

        # Result label
        self.convert_result = tk.Label(form_frame, text="", 
        font=("Helvetica", 16, "bold"), bg=COLORS['card_bg'], fg=COLORS['primary'])
        self.convert_result.pack(pady=20)

    def create_settings_tab(self):
        # Main container
        main_frame = ttk.Frame(self.settings_frame, style='Card.TFrame')
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)

        # Title
        title_label = tk.Label(main_frame, text="Settings", 
        font=("Helvetica", 24, "bold"), bg=COLORS['card_bg'], fg=COLORS['primary'])
        title_label.pack(pady=20)

        # Currency settings
        currency_frame = ttk.LabelFrame(main_frame, text="Default Currency", padding=20)
        currency_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(currency_frame, text="Select default currency:", 
        font=("Helvetica", 12)).pack(pady=5)
        currency_combo = ttk.Combobox(currency_frame, textvariable=self.default_currency, 
        values=self.currencies, state="readonly", width=10, font=("Helvetica", 12))
        currency_combo.pack(pady=5)
        currency_combo.bind('<<ComboboxSelected>>', lambda e: self.update_all_amounts())

        # Category management
        category_frame = ttk.LabelFrame(main_frame, text="Categories", padding=20)
        category_frame.pack(fill=tk.X, pady=10)

        # Add category
        add_category_frame = ttk.Frame(category_frame)
        add_category_frame.pack(pady=5)
        ttk.Label(add_category_frame, text="Add new category:", 
        font=("Helvetica", 12)).pack(side=tk.LEFT, padx=5)
        self.new_category = ttk.Entry(add_category_frame, font=("Helvetica", 12))
        self.new_category.pack(side=tk.LEFT, padx=5)
        add_button = tk.Button(add_category_frame, text="Add", 
        bg=COLORS['primary'], fg=COLORS['white'], font=("Helvetica", 10, "bold"),
        command=self.add_category, relief="flat", padx=10, pady=5)
        add_button.pack(side=tk.LEFT, padx=5)
        add_button.bind('<Enter>', lambda e: add_button.configure(bg=COLORS['hover']))
        add_button.bind('<Leave>', lambda e: add_button.configure(bg=COLORS['primary']))

        # Category list
        self.category_listbox = tk.Listbox(category_frame, height=5, 
        font=("Helvetica", 12), bg=COLORS['white'], fg=COLORS['text'])
        self.category_listbox.pack(pady=5, fill=tk.X)
        self.update_category_list()

    def update_category_list(self):
        self.category_listbox.delete(0, tk.END)
        for category in self.categories:
            self.category_listbox.insert(tk.END, category)

    def add_category(self):
        new_category = self.new_category.get().strip()
        if new_category and new_category not in self.categories:
            self.categories.append(new_category)
            self.update_category_list()
            self.new_category.delete(0, tk.END)
        else:
            self.show_error_message("Invalid category name or category already exists")

    def apply_filters(self):
        # Clear current display
        for item in self.expenses_incomes_list.get_children():
            self.expenses_incomes_list.delete(item)

        search_term = self.search_var.get().lower()
        filter_type = self.filter_type_var.get()
        filter_category = self.filter_category_var.get()

        for transaction in self.transactions:
            # Apply filters
            if filter_type != "All" and transaction.transaction_type != filter_type:
                continue
            if filter_category != "All" and transaction.category != filter_category:
                continue
            if search_term and search_term not in transaction.description.lower():
                continue

            # Add to Treeview if passes filters
            self.expenses_incomes_list.insert("", "end", values=(
                transaction.date,
                transaction.transaction_type,
                transaction.amount,
                transaction.currency,
                transaction.category,
                transaction.description
            ))

    def add_transaction(self):
        # Get transaction type, amount, description, category, and currency from the UI
        transaction_type = self.transaction_var.get()
        amount_entry_text = self.amountEntry.get()
        description_entry_text = self.descriptionEntry.get()
        category = self.category_var.get()
        currency = self.default_currency.get()

        try:
            amount = float(amount_entry_text)
        except ValueError:
            self.show_error_message("Invalid amount. Please enter a numeric value.")
            return

        if not amount_entry_text or amount <= 0:
            self.show_error_message("Amount cannot be empty or non-positive")
            return

        if not transaction_type:
            self.show_error_message("Please select a transaction type")
            return

        # Create a Transaction object and update UI
        transaction = Transaction(transaction_type, amount_entry_text, 
        description_entry_text, category, currency)
        self.transactions.append(transaction)

        # Convert amount to default currency for totals
        converted_amount = self.convert_to_default_currency(amount, currency)

        # Insert into Treeview with date, category, and currency
        self.expenses_incomes_list.insert("", "end", values=(
            transaction.date,
            transaction_type,
            amount_entry_text,
            currency,
            category,
            description_entry_text
        ))

        if transaction_type == "Expense":
            self.total_expenses.set(self.total_expenses.get() + converted_amount)
        else:
            self.total_incomes.set(self.total_incomes.get() + converted_amount)

        self.total_balance.set(self.total_incomes.get() - self.total_expenses.get())
        
        # Save transactions
        self.save_transactions()
        self.update_visualization()  # Update visualization when new transaction is added

        # Clear entries
        self.amountEntry.delete(0, "end")
        self.descriptionEntry.delete(0, "end")

    def delete_transaction(self):
        selected_item = self.expenses_incomes_list.selection()
        if not selected_item:
            self.show_error_message("Please select a transaction to delete")
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this transaction?"):
            item = selected_item[0]
            values = self.expenses_incomes_list.item(item)['values']
            
            # Update totals
            amount = float(values[2])
            if values[1] == "Expense":
                self.total_expenses.set(self.total_expenses.get() - amount)
            else:
                self.total_incomes.set(self.total_incomes.get() - amount)
            
            self.total_balance.set(self.total_incomes.get() - self.total_expenses.get())
            
            # Remove from list and Treeview
            self.transactions = [t for t in self.transactions if t.date != values[0]]
            self.expenses_incomes_list.delete(item)
            
            # Save changes
            self.save_transactions()
            self.update_visualization()  # Update visualization when transaction is deleted

    def edit_transaction(self):
        selected_item = self.expenses_incomes_list.selection()
        if not selected_item:
            self.show_error_message("Please select a transaction to edit")
            return

        item = selected_item[0]
        values = self.expenses_incomes_list.item(item)['values']
        
        # Create edit window
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Edit Transaction")
        edit_window.geometry("300x200")

        # Create entry fields
        ttk.Label(edit_window, text="Type:").pack(pady=5)
        type_var = tk.StringVar(value=values[1])
        type_frame = ttk.Frame(edit_window)
        type_frame.pack(pady=5)
        ttk.Radiobutton(type_frame, text="Expense", variable=type_var, value="Expense").pack(side=tk.LEFT)
        ttk.Radiobutton(type_frame, text="Income", variable=type_var, value="Income").pack(side=tk.LEFT)

        ttk.Label(edit_window, text="Amount:").pack(pady=5)
        amount_entry = ttk.Entry(edit_window)
        amount_entry.insert(0, values[2])
        amount_entry.pack(pady=5)

        ttk.Label(edit_window, text="Description:").pack(pady=5)
        desc_entry = ttk.Entry(edit_window)
        desc_entry.insert(0, values[3])
        desc_entry.pack(pady=5)

        def save_changes():
            try:
                new_amount = float(amount_entry.get())
                if new_amount <= 0:
                    raise ValueError("Amount must be positive")
                
                # Update totals
                old_amount = float(values[2])
                if values[1] == "Expense":
                    self.total_expenses.set(self.total_expenses.get() - old_amount)
                else:
                    self.total_incomes.set(self.total_incomes.get() - old_amount)

                new_type = type_var.get()
                if new_type == "Expense":
                    self.total_expenses.set(self.total_expenses.get() + new_amount)
                else:
                    self.total_incomes.set(self.total_incomes.get() + new_amount)

                self.total_balance.set(self.total_incomes.get() - self.total_expenses.get())

                # Update transaction in list
                for t in self.transactions:
                    if t.date == values[0]:
                        t.transaction_type = new_type
                        t.amount = new_amount
                        t.description = desc_entry.get()
                        break

                # Update Treeview
                self.expenses_incomes_list.item(item, values=(
                    values[0],
                    new_type,
                    new_amount,
                    values[3],
                    values[4],
                    desc_entry.get()
                ))

                self.save_transactions()
                edit_window.destroy()
                self.update_visualization()  # Update visualization when transaction is edited
            except ValueError as e:
                self.show_error_message(str(e))

        ttk.Button(edit_window, text="Save Changes", command=save_changes).pack(pady=10)

    def clear_all_transactions(self):
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear all transactions?"):
            self.transactions.clear()
            for item in self.expenses_incomes_list.get_children():
                self.expenses_incomes_list.delete(item)
            self.total_expenses.set(0)
            self.total_incomes.set(0)
            self.total_balance.set(0)
            self.save_transactions()
            self.update_visualization()  # Update visualization when all transactions are cleared

    def save_transactions(self):
        transactions_data = []
        for transaction in self.transactions:
            transactions_data.append({
                'type': transaction.transaction_type,
                'amount': transaction.amount,
                'description': transaction.description,
                'category': transaction.category,
                'currency': transaction.currency,
                'date': transaction.date
            })
        
        with open('transactions.json', 'w') as f:
            json.dump(transactions_data, f)

    def load_transactions(self):
        try:
            if os.path.exists('transactions.json'):
                with open('transactions.json', 'r') as f:
                    transactions_data = json.load(f)
                    
                for data in transactions_data:
                    transaction = Transaction(
                        data['type'],
                        data['amount'],
                        data['description'],
                        data['category'],
                        data.get('currency', 'INR'),  # Default to INR for old transactions
                        data['date']
                    )
                    self.transactions.append(transaction)
                    
                    # Convert amount to default currency for totals
                    converted_amount = self.convert_to_default_currency(
                        transaction.amount, transaction.currency)
                    
                    # Update UI
                    self.expenses_incomes_list.insert("", "end", values=(
                        transaction.date,
                        transaction.transaction_type,
                        transaction.amount,
                        transaction.currency,
                        transaction.category,
                        transaction.description
                    ))
                    
                    # Update totals
                    if transaction.transaction_type == "Expense":
                        self.total_expenses.set(self.total_expenses.get() + converted_amount)
                    else:
                        self.total_incomes.set(self.total_incomes.get() + converted_amount)
                
                self.total_balance.set(self.total_incomes.get() - self.total_expenses.get())
        except Exception as e:
            self.show_error_message(f"Error loading transactions: {str(e)}")

    def convert_currency(self):
        try:
            amount = float(self.convert_amount.get())
            from_curr = self.from_currency.get()
            to_curr = self.to_currency.get()

            # Convert to INR first (as base currency)
            inr_amount = amount / self.currency_rates[from_curr]
            # Convert from INR to target currency
            converted_amount = inr_amount * self.currency_rates[to_curr]

            self.convert_result.config(
                text=f"{amount:.2f} {from_curr} = {converted_amount:.2f} {to_curr}")
        except ValueError:
            self.show_error_message("Please enter a valid amount")
        except Exception as e:
            self.show_error_message(f"Error converting currency: {str(e)}")

    def convert_to_default_currency(self, amount, from_currency):
        """Convert amount from given currency to default currency (INR)"""
        if from_currency == "INR":
            return float(amount)
        return float(amount) * self.currency_rates["INR"] / self.currency_rates[from_currency]

    def update_all_amounts(self):
        """Update all displayed amounts when default currency changes"""
        self.total_expenses.set(0)
        self.total_incomes.set(0)
        
        for transaction in self.transactions:
            amount = self.convert_to_default_currency(transaction.amount, transaction.currency)
            if transaction.transaction_type == "Expense":
                self.total_expenses.set(self.total_expenses.get() + amount)
            else:
                self.total_incomes.set(self.total_incomes.get() + amount)
        
        self.total_balance.set(self.total_incomes.get() - self.total_expenses.get())
        self.apply_filters()

    def show_error_message(self, message):
        tk.messagebox.showerror("Error", message)

    def load_currency_rates(self):
        """Load currency rates from API or use fallback rates"""
        try:
            # Using a free currency API
            response = requests.get("https://api.exchangerate-api.com/v4/latest/INR")
            if response.status_code == 200:
                self.currency_rates = response.json()["rates"]
            else:
                # Fallback rates if API fails (INR as base)
                self.currency_rates = {
                    "INR": 1.0,
                    "USD": 0.012,
                    "EUR": 0.011,
                    "GBP": 0.0096,
                    "JPY": 1.78,
                    "AUD": 0.018,
                    "CAD": 0.016,
                    "CHF": 0.011,
                    "CNY": 0.086
                }
        except:
            # Fallback rates if API fails (INR as base)
            self.currency_rates = {
                "INR": 1.0,
                "USD": 0.012,
                "EUR": 0.011,
                "GBP": 0.0096,
                "JPY": 1.78,
                "AUD": 0.018,
                "CAD": 0.016,
                "CHF": 0.011,
                "CNY": 0.086
            }

    def create_visualization_tab(self):
        # Main container
        main_frame = ttk.Frame(self.visualization_frame, style='Card.TFrame')
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)

        # Title
        title_label = tk.Label(main_frame, text="Expense/Income Visualization", 
        font=("Helvetica", 24, "bold"), bg=COLORS['card_bg'], fg=COLORS['primary'])
        title_label.pack(pady=20)

        # Create frame for the graph
        graph_frame = ttk.Frame(main_frame, style='Card.TFrame')
        graph_frame.pack(expand=True, fill='both', padx=20, pady=20)

        # Create matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(expand=True, fill='both')

        # Create button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)

        # Add visualization button
        visualize_btn = tk.Button(button_frame, text="Update Visualization", 
        bg=COLORS['primary'], fg=COLORS['white'], font=("Helvetica", 12, "bold"), 
        command=self.update_visualization, relief="flat", padx=20, pady=10)
        visualize_btn.pack(pady=10)
        visualize_btn.bind('<Enter>', lambda e: visualize_btn.configure(bg=COLORS['hover']))
        visualize_btn.bind('<Leave>', lambda e: visualize_btn.configure(bg=COLORS['primary']))

    def update_visualization(self):
        # Clear previous plot
        self.ax.clear()

        # Group transactions by category
        category_data = defaultdict(lambda: {'expense': 0, 'income': 0})
        for transaction in self.transactions:
            amount = float(transaction.amount)
            if transaction.transaction_type == "Expense":
                category_data[transaction.category]['expense'] += amount
            else:
                category_data[transaction.category]['income'] += amount

        # Prepare data for plotting
        categories = list(category_data.keys())
        expenses = [category_data[cat]['expense'] for cat in categories]
        incomes = [category_data[cat]['income'] for cat in categories]

        # Set up bar positions
        x = range(len(categories))
        width = 0.35

        # Plot bars
        self.ax.bar([i - width/2 for i in x], expenses, width, label='Expenses', color=COLORS['danger'])
        self.ax.bar([i + width/2 for i in x], incomes, width, label='Income', color=COLORS['success'])

        # Customize the plot
        self.ax.set_xlabel('Categories')
        self.ax.set_ylabel('Amount')
        self.ax.set_title('Expenses and Income by Category')
        self.ax.set_xticks(x)
        self.ax.set_xticklabels(categories, rotation=45, ha='right')
        self.ax.legend()

        # Add grid
        self.ax.grid(True, linestyle='--', alpha=0.7)

        # Adjust layout
        plt.tight_layout()

        # Update canvas
        self.canvas.draw()




if __name__ == "__main__":
    root = tk.Tk()
    app = ExpensesIncomesTracker(root)
    root.mainloop()
