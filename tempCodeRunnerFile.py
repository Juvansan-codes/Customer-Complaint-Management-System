  # Keep one center cell so form stays in the middle of the window
    root.grid_rowconfigure(0, weight=1)
    root.grid_rowconfigure(1, weight=0)
    root.grid_rowconfigure(2, weight=1)
    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=0)
    root.grid_columnconfigure(2, weight=1)

    # Simple form group for clean alignment
    form_frame = tk.Frame(root)
    form_frame.grid(row=1, column=1)

    tk.Label(form_frame, text="Login Page", font=("Arial", 16, "bold")).grid(
        row=0, column=0, columnspan=2, pady=(0, 15)
    )
    tk.Label(form_frame, text="Username").grid(row=1, column=0, padx=(0, 10), pady=6, sticky="e")
    username_entry = tk.Entry(form_frame, width=30)
    username_entry.grid(row=1, column=1, pady=6, sticky="w")
    tk.Label(form_frame, text="Password").grid(row=2, column=0, padx=(0, 10), pady=6, sticky="e")
    password_entry = tk.Entry(form_frame, width=30, show="*")
    password_entry.grid(row=2, column=1, pady=6, sticky="w")
    tk.Button(
        form_frame,
        text="Login",
        command=lambda: login_user(username_entry.get(), password_entry.get()),
    ).grid(row=3, column=0, columnspan=2, pady=(12, 6))
    tk.Button(form_frame, text="Go to Register", command=show_register_page).grid(
        row=4, column=0, columnspan=2, pady=(4, 0)
    )

