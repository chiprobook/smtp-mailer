import flet as ft
from flet import *
import smtplib
import imaplib
import asyncio
import sqlite3
import time


from email import encoders
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart

class setup_database():
    def __init__(self):
        conn = sqlite3.connect('ShowMeGrace.db')
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Grace (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
        ''')
        conn.commit()
        conn.close()

setup_database()

class LoadingOverlay:
    def __init__(self, page):
        self.page = page
        self.overlay = None

    def show(self):
        self.overlay = Container(
            content=Container(
                content=Column(
                    controls=[
                        ProgressRing(),  # Loading spinner
                        #ft.Text("Sending email...", style=ft.TextThemeStyle.DISPLAY_SMALL)
                    ],
                    alignment=MainAxisAlignment.CENTER,
                    horizontal_alignment=CrossAxisAlignment.CENTER
                ),
                alignment=alignment.center,
                padding=50
            ),
            bgcolor=colors.BLACK12,
            expand=True
        )
        self.page.overlay.append(self.overlay)
        self.page.update()

    def hide(self):
        if self.overlay in self.page.overlay:
            self.page.overlay.remove(self.overlay)
            self.page.update()

class Messagebox(Container):
    def __init__(self, text, page):
        super().__init__()
        self.page = page
        self.text = Text(value=text, color=colors.WHITE)
        self.container = Container(
            content=Container(
                content=Column(
                    controls=[self.text
                    ],
                    alignment=MainAxisAlignment.CENTER,
                    horizontal_alignment=CrossAxisAlignment.CENTER
                ),
                alignment=alignment.center,
                padding=50
            ),
            bgcolor=colors.BLACK12,
            expand=True
        )         
        self.page.overlay.append(self.container)
        self.page.update()
        asyncio.run(self.hide_message())

    async def hide_message(self):
        await asyncio.sleep(3)
        self.page.overlay.remove(self.container)
        self.page.update()

class Startup:
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page    
        self.page.horizontal_alignment = CrossAxisAlignment.CENTER
        self.page.update()

        self.loggin = False
        self.email_content_width = None

        self.draft_mail_view = Container(
            content=Column(
                controls=[]
            )
        )
        self.sent_mail_view = Container(
            content=Column(
                controls=[]
            )
        )
        self.outbox_mail_view = Container(
            content=Column(
                controls=[]
            )
        )
        self.selected_emails = []
        self.outbox_emails = []
        self.sent_emails = []
        self.drafts = []

        self.outbox_save_emails = []
        self.sent_save_emails = []
        self.draft_save_emails =[]

        self.dialog = ft.FilePicker(on_result=self.handle_file_picked) 
        self.page.overlay.append(self.dialog)

        self.loading_overlay = LoadingOverlay(page)
       
        self.init_content()
        self.load_mail_form()

    def init_content(self):
        self.page.controls.clear()
        self.navigation_rail_expanded = True

        self.navigation_rail = NavigationRail(
            selected_index=0,
            leading=Container( 
                content=IconButton( 
                    icon=icons.MENU, on_click=lambda _: self.toggle_navigation_rail(),
                    icon_size=30 
                ),
                alignment=ft.alignment.top_right, 
                padding=10,
            ),
            destinations=[
                NavigationRailDestination(icon=icons.INBOX, label="Inbox"),
                NavigationRailDestination(icon=icons.ACCOUNT_CIRCLE, label="Accounts"),
                NavigationRailDestination(icon=icons.DRAFTS, label="Draft"),
                NavigationRailDestination(icon=icons.OUTBOX, label="Outbox"),
                NavigationRailDestination(icon=icons.SEND, label="Sent"),
            ],
            label_type=NavigationRailLabelType.ALL if self.navigation_rail_expanded else NavigationRailLabelType.NONE,
            extended=self.navigation_rail_expanded,
            on_change=self.on_navigation_change,
            bgcolor=colors.BROWN_500
        )
        self.main_area = Container(
            content=Column(
                controls=[], 
                alignment=alignment.center, 
                expand=True 
                ), 
            expand=True 
        )
        self.main_content_icon = Column(
            controls=[
                Container(
                    content=IconButton(icon=icons.ADD, icon_size=70, on_click=lambda e: self.load_mail_form()), 
                    alignment=alignment.top_right, 
                    padding=10
                )
            ]
        )
        self.appbar = AppBar( 
            title=Text("Whaya Mail", style={"size": 24, "weight": "bold"}), 
            leading=Icon(name="mail_outline"), 
            actions=[ 
                PopupMenuButton(
                    content=Text("Add Account"), 
                    items=[
                        PopupMenuItem(text="Gmail", on_click=lambda e: self.handle_add_account(e, "gmail")), 
                        PopupMenuItem(text="Outlook", on_click=lambda e: self.handle_add_account(e, "outlook")), 
                        PopupMenuItem(text="Yahoo", on_click=lambda e: self.handle_add_account(e, "yahoo")), 
                        PopupMenuItem(text="ProtonMail", on_click=lambda e: self.handle_add_account(e, "protonmail")), 
                        PopupMenuItem(text="AOL", on_click=lambda e: self.handle_add_account(e, "aol")), 
                        PopupMenuItem(text="Zoho", on_click=lambda e: self.handle_add_account(e, "zoho")), 
                        PopupMenuItem(text="Yandex", on_click=lambda e: self.handle_add_account(e, "yandex")) 
                    ]
                ), 
                PopupMenuButton( 
                    items=[ 
                        PopupMenuItem(text="Login", on_click=lambda e: self.login(e)), 
                        PopupMenuItem(text="Signup", on_click=lambda e: self.signup(e))
                    ] 
                ) 
            ],
            bgcolor=colors.BROWN_300, 
            color=colors.WHITE
        )
        self.main_background = Container( 
            content=Column( 
                controls=[ 
                    Row( 
                        controls=[self.navigation_rail, self.main_area, self.main_content_icon], 
                        alignment=MainAxisAlignment.SPACE_EVENLY, 
                        expand=True,
                        spacing=0,
                        ) 
                    ], 
                    expand=True 
                ), 
                gradient=LinearGradient( 
                    colors=[colors.WHITE, colors.BROWN_100], 
                    begin=alignment.center_left, end=alignment.center_right, 
                    ), 
                    expand=True 
            ) 
        self.page.appbar = self.appbar
        self.page.controls.append(self.main_background)
        self.page.update()

    def handle_add_account(self, e, provider):
        if self.loggin == False:
            self.login(e)
        else:
            self.initial_oauth(provider) 

    def initial_oauth(self, provider):
        if provider == "gmail": 
            self.page.launch_url("https://accounts.google.com/o/oauth2/auth")
        elif provider == "outlook":
            self.page.launch_url()
        elif provider == "yahoo":
            self.page.launch_url()
        elif provider == "hotmail":
            self.page.launch_url()
        elif provider == "protomail":
            self.page.launch_url()
        elif provider == "aol":
            self.page.launch_url()
        elif provider == "zoho":
            self.page.launch_url()
        elif provider == "yandex":
            self.page.launch.url()
        else:
            self.init_content()

    def on_navigation_change(self, e): 
        if e.control.selected_index == 0: 
            self.show_inbox_button(e) 
        elif e.control.selected_index == 1: 
            self.load_account(e)
        elif e.control.selected_index == 2:
            self.show_drafts_button(e)
        elif e.control.selected_index == 3:
            self.show_outbox_button(e)
        elif e.control.selected_index == 4:
            self.show_sent_button(e)

    def toggle_navigation_rail(self):
        self.navigation_rail_expanded = not self.navigation_rail_expanded
        self.navigation_rail.label_type = NavigationRailLabelType.ALL if self.navigation_rail_expanded else NavigationRailLabelType.NONE
        self.navigation_rail.extended = self.navigation_rail_expanded

        if hasattr(self, 'email_content_page'): 
            self.email_content_width = self.page.width * 0.5 if self.navigation_rail_expanded else self.page.width * 0.7
            self.email_content_page.width = self.email_content_width 
            self.page.update()

    def load_mail_form(self, draft=None, forward=None, account=None):
        self.main_area.content.controls.clear()
        self.attachment_file = None

        self.server = TextField(label="Server", width=250, hint_text="Enter server address", border=InputBorder.UNDERLINE, visible=False)
        self.auto_server = ft.Dropdown(
            options=[
               dropdown.Option(key="smtp.gmail.com", text="Gmail"), 
               dropdown.Option(key="smtp.yahoo.com", text="Yahoo"),
               dropdown.Option(key="smtp.mailgun.org", text="Mailgun"),
               dropdown.Option(key="smtp.office365.com", text="Outlook"),
               dropdown.Option(key="smtp.aol.com", text="Aol"),
               dropdown.Option(key="smtp.zoho.com", text="Zoho"),
               dropdown.Option(key="smtp.sendgrid.net", text="SendGrid"),
               dropdown.Option(key="email-smtp.us-east-1.amazonaws.com", text="Amazon"),
               dropdown.Option(key="custom", text="Custom")
            ],
            label="SMTP Server",
            width=250,
            hint_text="Enter SMTP server or select from options",
            on_change=self.server_changed
        )
        self.port = TextField(label="Port", width=200, hint_text="Enter port number", border=InputBorder.UNDERLINE, visible=False)
        self.auto_port = ft.Dropdown(
            options=[
               dropdown.Option(key="25", text="25"), 
               dropdown.Option(key="587", text="587"),
               dropdown.Option(key="465", text="465"),
               dropdown.Option(key="custom", text="Custom")
            ],
            label="Port",
            width=100,
            on_change=self.port_changed
        )
        self.user = TextField(label="User", width=250, hint_text="Enter username", border=InputBorder.UNDERLINE)
        self.password = TextField(label="Password", width=250, password=True, can_reveal_password=True, hint_text="Enter password", border=InputBorder.UNDERLINE)
        self.recipient = TextField(label="Recipient", width=500, height=70, multiline=True, hint_text="Enter recipient email", border=InputBorder.UNDERLINE)
        self.recipient_type = ft.Dropdown( 
            options=[
                dropdown.Option(key="To", text="To"), 
                dropdown.Option(key="Cc", text="Cc"),
                dropdown.Option(key="Bcc", text="Bcc")
            ], 
            label="Type", 
            width=100 
        )
        self.replyto = TextField(label="Reply-To", width=250, hint_text="Optional", border=InputBorder.UNDERLINE)
        self.subject = TextField(label="Subject", width=500, border=InputBorder.UNDERLINE, filled=True, hint_text="Enter subject")
        self.body = TextField(label="Body", width=900, height=self.page.height * 0.45, border=InputBorder.UNDERLINE, multiline=True, 
            filled=True, hint_text="Enter message body")
        
        self.sendbutton = IconButton(icon=icons.SEND, icon_size=30, tooltip="send", on_click=lambda e: self.send_mail(e))
        self.savedraft = IconButton(icon=icons.SAVE, icon_size=30, tooltip="save", on_click=lambda e: self.load_draft_field(e))
        self.error_message = Text(value="", color=ft.colors.BLACK)
        self.attachment_button = IconButton(icon=icons.ATTACH_FILE, icon_size=30, tooltip="attachment", on_click=lambda e: self.load_attachment())
        self.form_back_button = IconButton(icon=ft.icons.CANCEL, icon_size=30, on_click=lambda e: self.init_content())


        if draft:
            self.server.value = draft["Server"]
            self.port.value = draft["Port"]
            self.user.value = draft["User"]
            self.password.value = draft["Password"]
            self.recipient.value = draft["Recipient"]
            self.replyto.value = draft["Replyto"]
            self.subject.value = draft["Subject"]
            self.body.value = draft["Body"]

        if forward: 
            self.subject.value = f"Fwd: {forward['Subject']}" 
            self.body.value = f"\n\n--- Forwarded Message ---\n{forward['Body']}"

        if account:
            self.server.value = account["Server"]
            self.user.value = account["User"]
            self.password.value = account["Password"]

        self.main_content = Container(
            content=Column(
                controls=[Row(controls=[self.form_back_button, Text(), Text(), Text(), Text(), Text(), Text(),
                        self.attachment_button, self.savedraft, self.sendbutton], 
                        alignment=MainAxisAlignment.START,
                    ),                
                    Row(controls=[self.auto_server, self.server, self.auto_port, self.port], alignment=ft.MainAxisAlignment.START),
                    Row(controls=[self.user, self.password], alignment=ft.MainAxisAlignment.START),
                    Row(controls=[self.replyto], alignment=ft.MainAxisAlignment.START),
                    Row(controls=[self.recipient, self.recipient_type], alignment=MainAxisAlignment.START),
                    self.subject, 
                    self.body,
                    self.error_message
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                expand=True,
                spacing=5
            ),
        ) 
        self.main_area.content.controls.append(self.main_content)
        self.page.update()

    def load_attachment(self): 
        self.dialog.pick_files()

    def handle_file_picked(self, e): 
        if e.files:
            self.attachment_file = e.files[0]
            self.body.value += f"\n{self.attachment_file.name}"
            self.page.update()

    def validate_fields(self):
        if not self.recipient_type.value:
            self.error_message.value = "Recipient type is required"
            self.page.update()
            return False 
        if not self.recipient.value.strip():
             self.error_message.value = "Recipient is required." 
             self.page.update() 
             return False 
        if not self.subject.value.strip(): 
            self.error_message.value = "Subject is required." 
            self.page.update() 
            return False 
        if not self.body.value.strip(): 
            self.error_message.value = "Body is required." 
            self.page.update() 
            return False 
        if not self.user.value.strip():
            self.error_message.value = "Username is required"
            self.page.update()
            return False
        if not self.password.value.strip():
            self.error_message.value = "Password is required"
            self.page.update()
            return False
        if self.auto_server.value == "custom" and not self.server.value.strip(): 
            self.error_message.value = "Server is required." 
            self.page.update() 
            return False 
        if not self.auto_server.value and not self.server.value.strip(): 
            self.error_message.value = "Server is required." 
            self.page.update() 
            return False 
        if self.auto_port.value == "custom" and not self.port.value.strip(): 
            self.error_message.value = "Port is required." 
            self.page.update() 
            return False 
        if not self.auto_port.value and not self.port.value.strip(): 
            self.error_message.value = "Port is required." 
            self.page.update() 
            return False
        return True

    def send_mail(self, e):
        if self.validate_fields():
            Messagebox("Processing", self.page)
            self.msg = MIMEMultipart()
            
            recipient_type = self.recipient_type.value 
            if recipient_type == "To": 
                self.msg["To"] = self.recipient.value 
            elif recipient_type == "Cc": 
                self.msg["Cc"] = ', '.join(self.recipient.value.split(',')) 
            elif recipient_type == "Bcc": 
                self.msg["Bcc"] = ', '.join(self.recipient.value.split(','))
            
            self.msg["From"] = self.user.value
            self.msg["Subject"] = self.subject.value
            self.msg.add_header("Reply-to", self.replyto.value)
            self.msg.attach(MIMEText(self.body.value, "plain"))

            if self.attachment_file: 
                filename = self.attachment_file.name
                with open(self.attachment_file.path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream') 
                    part.set_payload(attachment.read()) 
                encoders.encode_base64(part) 
                part.add_header('Content-Disposition', f"attachment; filename= {filename}")       
                self.msg.attach(part)
        
            try:
                self.loading_overlay.show()
                if self.auto_server.value == "custom": 
                    server = self.server.value 
                else: 
                    server = self.auto_server.value 
                    
                if self.auto_port.value == "custom": 
                    port = self.port.value 
                else:
                    port = self.auto_port.value

                self.Server = smtplib.SMTP(server, port)
                self.Server.starttls()
                self.Server.login(self.user.value, self.password.value)
                for i in self.recipient.value.strip():
                    Messagebox(f"Sending to: {i}", self.page)
                self.Server.send_message(self.msg)
                self.Server.quit()
                Messagebox("Email sent successfully!", self.page)
                self.save_sent_email(e)
                self.loading_overlay.hide()
                self.page.update()
                
            except Exception as e:
                Messagebox(f"Email failed, saved in outbox: {e}", self.page)
                self.save_outbox_mail(e)
                self.loading_overlay.hide()
                self.page.update()

            self.error_message.value = ""
            self.page.update()
        else:
            self.page.update()

    def remove_overlay(self, content):
        self.page.overlay.remove(content)
        self.page.update()

    def close_main_content_icon(self, origin):
        if origin == "outbox":
            self.main_content_icon.controls.clear()
            self.init_content()  
            self.show_outbox_button(None)
        elif origin == "sent":
            self.main_content_icon.controls.clear()
            self.init_content()  
            self.show_sent_button(None)
        elif origin == "inbox":
            self.main_content_icon.controls.clear()
            self.show_inbox_button(None)
        else:
            self.main_content_icon.controls.clear()   
        self.page.update()

    def forward_email(self, msg):
        if isinstance(msg, dict):
            forward_data = {
                "Subject": msg["Subject"],
                "Body": msg["Body"]
            }
        else:
            if msg.is_multipart():
                body = ""
                attachments = []
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain":
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    elif content_type == "text/html":
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    elif content_type.startswith("image/"):
                        filename = part.get_filename()
                        attachments.append({"type": "image", "filename": filename, "data": part.get_payload(decode=True)})
                    elif content_type == "application/json":
                        json_data = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        attachments.append({"type": "json", "data": json_data})
                    elif content_type == "application/pdf":
                        filename = part.get_filename()
                        attachments.append({"type": "pdf", "filename": filename, "data": part.get_payload(decode=True)})
                    elif content_type.startswith("audio/"):
                        filename = part.get_filename()
                        attachments.append({"type": "audio", "filename": filename, "data": part.get_payload(decode=True)})

                forward_data = {
                    "Subject": msg["Subject"],
                    "Body": body,
                    "Attachments": attachments
                }
            else:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                forward_data = {
                    "Subject": msg["Subject"],
                    "Body": body
                }
        self.init_content()
        self.load_mail_form(forward=forward_data)

    def load_account(self, e):
        pass

    def show_inbox_button(self, e):
        self.main_area.content.controls.clear()
        self.selected_emails = []

        self.delete_button = IconButton(icon=icons.DELETE, on_click=self.delete_inbox, visible=False)
        self.select_button = IconButton(icon=icons.CHECK_BOX, on_click=self.toggle_select_mode)
        self.search_bar = TextField(hint_text="Search...", width=250, bgcolor=colors.BLACK12, on_change=self.search_inbox) 
        self.select_all_button = IconButton(icon=icons.CHECK_BOX, on_click=lambda e: self.select_all_inbox, visible=False)
    
        self.controls_row = Container(
            content=Row(
                controls=[
                    self.search_bar,
                    self.select_button,
                ],
                alignment=MainAxisAlignment.SPACE_EVENLY,
                spacing=10
            ),
            border_radius=5,
            shadow=[ft.BoxShadow(color=ft.colors.GREY, blur_radius=2)],
            bgcolor=colors.WHITE,
            padding=2,
            margin=5
        )

        self.load_mail_content = [self.controls_row]
        if not self.inbox_emails: 
            self.load_mail_content.append( 
                Container( 
                    content=Text("inbox is empty", text_align=TextAlign, color=colors.BLACK87), 
                    alignment=alignment.center,
                    bgcolor=colors.WHITE
                ) 
            )
        else:
            self.update_inbox_content(self.inbox_emails)

        self.mail_view_width = self.page.width * 0.3
        self.mail_view = ft.Container( 
            content=ft.Column( 
                controls=self.load_mail_content + [ 
                    ft.Row(controls=[self.select_all_button, self.delete_button], 
                        alignment=MainAxisAlignment.SPACE_BETWEEN
                    ) 
                ], 
                spacing=10, 
                alignment=ft.MainAxisAlignment.START,
            ), 
            width=self.mail_view_width, 
            bgcolor=ft.colors.WHITE, 
            expand=True 
        )
        self.main_area.content.controls.append(self.mail_view)
        self.page.update()

    def search_inbox(self, e):
        search_query = e.control.value.lower()

        if not search_query:
            self.update_inbox_content(self.inbox_emails) 
            return

        filtered_emails = [
            email for email in self.inbox_emails 
            if (
                ('Subject' in email and search_query in email['Subject'].lower()) or
                ('To' in email and search_query in email['To'].lower()) or
                ('Body' in email and search_query in email['Body'].lower())
            )
        ]
        self.update_inbox_content(filtered_emails)

    def update_inbox_content(self, emails):
        self.load_mail_content = [self.controls_row]

        if not emails:
            self.load_mail_content.append(
                Container(
                    content=Text("No results found", text_align=TextAlign, color=colors.BLACK87),
                    alignment=alignment.center,
                )
            )
        else:
            self.mail_content_buttons = [ 
                Container( 
                    content=ft.Row( 
                        controls=[ 
                            Checkbox(value=False, visible=False, on_change=lambda e: self.toggle_email_selection(e, email)), 
                            email
                        ],
                        alignment=alignment.center_left
                    ) 
                ) 
                for email in self.inbox_emails
            ] 
            self.load_mail_content.extend(self.mail_content_buttons)

        self.mail_view.content.controls = self.load_mail_content + [
            ft.Row(controls=[self.select_all_button, self.delete_button], alignment=MainAxisAlignment.SPACE_BETWEEN)
        ]
        self.page.update()

    def select_all_inbox(self, e): 
        select_all_value = not all(email in self.selected_emails for email in self.inbox_emails)
        self.selected_emails = self.inbox_emails if select_all_value else [] 
        for mail_button in self.mail_content_buttons: 
            mail_button.content.controls[0].value = select_all_value 
            mail_button.update() 
        self.delete_button.visible = bool(self.selected_emails)
        self.page.update() 

    def delete_inbox(self, e): 
        self.inbox_emails = [email for email in self.inbox_emails if email not in self.selected_emails] 
        self.selected_emails = [] 
        self.show_inbox_button(None) 
        self.page.update()

    def load_inbox_button(self, msg):
        self.main_content_icon.controls.clear()

        self.back_button = IconButton(icon=icons.CANCEL, on_click=self.close_main_content_icon("inbox"), icon_size=30)
        self.reply_button = IconButton(icon=icons.REPLY, on_click=lambda _: self.reply_to_email(msg), icon_size=30) 
        self.forward_button = IconButton(icon=icons.FORWARD, on_click=lambda _: self.forward_email(msg), icon_size=30) 

        self.email_content_width = self.page.width * 0.5 if self.navigation_rail_expanded else self.page.width * 0.7
        load_inbox_view = ft.Container(
            content=ft.Column(
                controls=[
                    Row(controls=[self.back_button, self.reply_button, self.forward_button], alignment=alignment.top_right),
                    ft.Text(f"{msg['From']}"),
                    ft.Text(f"{msg['Subject']}"),
                    ft.Text(f"{msg.get_payload(decode=True).decode('utf-8', errors='ignore')}")
                ],
                spacing=10,
                alignment=ft.alignment.center,
                expand=True
            ),
            alignment=alignment.center_right,
            bgcolor=colors.WHITE,
            shadow=BoxShadow(blur_radius=10, spread_radius=2, color=colors.BLACK12),
            expand=True,
            width=self.email_content_width,
            height=self.page.height
        )

        self.main_content_icon.controls.append(load_inbox_view)
        self.page.update()

    def load_draft_field(self, e):
        self.page.overlay.clear()
        self.add_draft_fields = Container(
            content=Container(
                content=Column(
                    controls=[
                        TextField(label="Name", hint_text="Input name"),
                        Row(
                            controls=[
                                ElevatedButton(text="Save", on_click=self.save_draft_mail),
                                ElevatedButton(text="Cancel", on_click=lambda e: self.remove_overlay(self.add_draft_fields))
                            ],
                            alignment=MainAxisAlignment.CENTER
                        )
                    ],
                    alignment=MainAxisAlignment.CENTER,
                    horizontal_alignment=CrossAxisAlignment.CENTER
                ),
                width=self.page.width * 0.3,
                height=self.page.height * 0.3,
                padding=20,
                border_radius=10,
                bgcolor=colors.WHITE,
                shadow=BoxShadow(blur_radius=10, spread_radius=2, color=ft.colors.BLACK87)
            ),
            alignment=alignment.center,
            expand=True
        )
        self.page.overlay.append(self.add_draft_fields)
        self.page.update()

    def save_draft_mail(self, e):
        self.remove_overlay(self.add_draft_fields)
        self.loading_overlay.show()
        time.sleep(1)
        self.save_draft = {
        "Save_name": self.add_draft_fields.content.content.controls[0].value,
        "Server": self.server.value,
        "Port": self.port.value,
        "User": self.user.value,
        "Password": self.password.value,
        "Recipient": self.recipient.value,
        "Replyto": self.replyto.value,
        "Subject": self.subject.value,
        "Body": self.body.value
        }
        self.display_draft_button = f"{self.add_draft_fields.content.content.controls[0].value}\nSubject: {self.subject.value}\nBody: {self.body.value}"   
        self.draft_button = Container( 
            content=ft.TextButton( 
                text=self.display_draft_button, on_click=lambda e, draft=self.save_draft: self.load_mail_form(draft=draft) 
            ), 
            width=330,
            height=70,
            bgcolor=colors.GREY_100,
            padding=5,
            border_radius=5, 
            alignment=alignment.center_left,
        )
        self.drafts.append(self.draft_button)
        self.draft_save_emails.append(self.save_draft)

        self.loading_overlay.hide()
        Messagebox("Draft saved successfully!", self.page)
        self.page.update()

    def show_drafts_button(self, e):
        self.main_area.content.controls.clear()
        self.selected_emails = []

        self.delete_button = IconButton(icon=icons.DELETE, on_click=self.delete_draft, visible=False)
        self.select_button = IconButton(icon=icons.CHECK_BOX, on_click=self.toggle_select_draft)
        self.search_bar = TextField(hint_text="Search...", width=250, bgcolor=colors.BLACK12, color=colors.BLACK, on_change=self.search_drafts) 
        self.select_all_button = IconButton(icon=icons.CHECK_BOX, on_click=lambda e: self.select_all_draft(e), visible=False)
    
        self.draft_controls_row = Container(
            content=Row(
                controls=[
                    self.search_bar,
                    self.select_button,
                ],
                alignment=MainAxisAlignment.SPACE_EVENLY,
                spacing=10
            ),
            border_radius=5,
            shadow=[ft.BoxShadow(color=ft.colors.GREY, blur_radius=2)],
            bgcolor=colors.WHITE,
            padding=2,
            margin=5
        )

        self.load_draft_content = [self.draft_controls_row]
        if not self.drafts: 
            self.load_draft_content.append( 
                Container( 
                    content=Text("Draft is empty", text_align=TextAlign, color=colors.BLACK87), 
                    alignment=alignment.center,
                ) 
            )
        else:
            self.update_draft_content(self.drafts)

        self.draft_view_width = self.page.width * 0.3
        self.draft_mail_list = Container( 
            content=ListView( 
                controls=self.load_draft_content, 
                spacing=10, 
                expand=True
            ), 
            width=self.draft_view_width, 
            bgcolor=colors.WHITE, 
            height=self.page.height - 60,
            expand=True 
        ) 
        self.draft_mail_view = Container( 
            content=Column( 
                controls=[ 
                    self.draft_mail_list, 
                    ft.Row(controls=[self.select_all_button, self.delete_button], 
                    alignment=MainAxisAlignment.SPACE_BETWEEN) 
                ], 
                expand=True 
            ), 
            width=self.draft_view_width, 
            bgcolor=colors.WHITE, expand=True
        )
        self.main_area.content.controls.append(self.draft_mail_view)
        self.page.update()
        self.adjust_content_width()

    def search_drafts(self, e):
        draft_search_query = e.control.value.lower()

        if not draft_search_query:
            self.update_draft_content(self.drafts) 
            return

        draft_filtered_emails = [
            draft_search for draft_search in self.drafts 
            if (
                ("Save name" in draft_search and draft_search_query in draft_search["Save name"].lower()) or
                ("Subject" in draft_search and draft_search_query in draft_search["Subject"].lower()) or
                ("Body" in draft_search and draft_search_query in draft_search["Body"].lower())
            )
        ]
        draft_filtered_buttons = [ 
           draft_ui_element for draft_ui_element, draft_data in zip(self.drafts, self.draft_save_emails) if draft_data in draft_filtered_emails 
        ] 
        
        self.update_draft_content(draft_filtered_buttons)

    def update_draft_content(self, draft_emails):
        self.load_draft_content = [self.draft_controls_row]

        if not draft_emails:
            self.load_draft_content.append(
                Container(
                    content=Text("No results found", text_align=TextAlign, color=colors.BLACK87),
                    alignment=alignment.center,
                )
            )
        else:
            self.draft_content_buttons = [
                Container(
                    content=ft.Row(
                        controls=[
                            Checkbox(value=False, visible=False, on_change=lambda e, email=email: self.toggle_email_selection(e, email)),
                            email            
                        ]  
                    ),
                    padding=3,
                    alignment=alignment.center_left 
                )  
                for email in draft_emails
            ]
            self.load_draft_content.extend(self.draft_content_buttons)
    
        self.draft_mail_view.content.controls = self.load_draft_content 
        self.page.update()
        self.adjust_content_width()

    def toggle_email_selection(self, e, email): 
        if e.control.value: 
            self.selected_emails.append(email) 
        else: 
            self.selected_emails.remove(email) 
        self.delete_button.visible = bool(self.selected_emails) 
        self.page.update()
    
    def toggle_select_draft(self, e): 
        for draft_mail_button in self.draft_content_buttons: 
            draft_mail_button.content.controls[0].visible = not draft_mail_button.content.controls[0].visible
            draft_mail_button.update() 
        self.select_all_button.visible = not self.select_all_button.visible 
        self.delete_button.visible = not self.delete_button.visible 
        self.page.update()
    
    def select_all_draft(self, e): 
        select_all_value = not all(email in self.selected_emails for email in self.drafts) 
        self.selected_emails = self.drafts if select_all_value else [] 
        for draft_mail_button in self.draft_content_buttons: 
            draft_mail_button.content.controls[0].value = select_all_value 
            draft_mail_button.update() 
        self.delete_button.visible = bool(self.selected_emails)
        self.page.update() 
                
    def delete_draft(self, e): 
        self.drafts = [email for email in self.drafts if email not in self.selected_emails] 
        self.selected_emails = [] 
        self.show_drafts_button(None) 
        self.page.update()

    def save_sent_email(self, e):
        self.save_sent_content = {
            "To": self.recipient.value,
            "Subject": self.subject.value,
            "Body": self.body.value
        }
        self.display_sent_content = f"To: {self.recipient.value}\nSubject: {self.subject.value}\nBody: {self.body.value}"

        self.sent_button = Container( 
            content=ft.TextButton( 
                text=self.display_sent_content, on_click=lambda e, sent_list=self.save_sent_content: self.load_sent_button(sent_list) 
            ), 
            width=330,
            height=70,
            bgcolor=colors.GREY_100,
            padding=5,
            border_radius=5, 
            alignment=alignment.center_left,
        )
        self.sent_emails.append(self.sent_button)
        self.sent_save_emails.append(self.save_sent_content)
        self.page.update()

    def show_sent_button(self, e):
        self.main_area.content.controls.clear()
        self.selected_emails = []

        self.delete_button = IconButton(icon=icons.DELETE, on_click=self.delete_sent, visible=False)
        self.select_button = IconButton(icon=icons.CHECK_BOX, on_click=self.toggle_select_sent)
        self.search_bar = TextField(hint_text="Search...", width=250, bgcolor=colors.BLACK12, color=colors.BLACK, on_change=self.search_sent) 
        self.select_all_button = IconButton(icon=icons.CHECK_BOX, on_click=lambda e: self.select_all_sent(e), visible=False)
    
        self.sent_controls_row = Container(
            content=Row(
                controls=[
                    self.search_bar,
                    self.select_button,
                ],
                alignment=MainAxisAlignment.SPACE_EVENLY,
                spacing=10
            ),
            border_radius=5,
            shadow=[ft.BoxShadow(color=ft.colors.GREY, blur_radius=2)],
            bgcolor=colors.WHITE,
            padding=2,
            margin=5
        )

        self.load_sent_content = [self.sent_controls_row]
        if not self.sent_emails: 
            self.load_sent_content.append( 
                Container( 
                    content=Text("Sent is empty", text_align=TextAlign, color=colors.BLACK87), 
                    alignment=alignment.center,
                    bgcolor=colors.WHITE
                ) 
            )
        else:
            self.update_sent_content(self.sent_emails)

        self.sent_view_width = self.page.width * 0.3

        self.sent_mail_list = Container( 
            content=ListView( 
                controls=self.load_sent_content, 
                spacing=10, 
                expand=True
            ), 
            width=self.sent_view_width, 
            bgcolor=colors.WHITE, 
            height=self.page.height - 60,
            expand=True 
        ) 
        self.sent_mail_view = Container( 
            content=Column( 
                controls=[ 
                    self.sent_mail_list, 
                    ft.Row(controls=[self.select_all_button, self.delete_button], 
                    alignment=MainAxisAlignment.SPACE_BETWEEN) 
                ], 
                expand=True 
            ), 
            width=self.sent_view_width, 
            bgcolor=colors.WHITE, expand=True
        )
        self.main_area.content.controls.append(self.sent_mail_view)
        self.page.update()
        self.adjust_content_width()

    def search_sent(self, e):
        sent_search_query = e.control.value.lower()

        if not sent_search_query:
            self.update_sent_content(self.sent_emails) 
            return

        sent_filtered_emails = [
            sent_search for sent_search in self.sent_emails 
            if (
                ("Subject" in sent_search and sent_search_query in sent_search["Subject"].lower()) or
                ("To" in sent_search and sent_search_query in sent_search["To"].lower()) or
                ("Body" in sent_search and sent_search_query in sent_search["Body"].lower())
            )
        ]
        sent_filtered_buttons = [ 
           sent_ui_element for sent_ui_element, sent_data in zip(self.sent_emails, self.sent_save_emails) if sent_data in sent_filtered_emails 
        ] 
        
        self.update_sent_content(sent_filtered_buttons)

    def update_sent_content(self, sent_emails):
        self.load_sent_content = [self.sent_controls_row]

        if not sent_emails:
            self.load_sent_content.append(
                Container(
                    content=Text("No results found", text_align=TextAlign, color=colors.BLACK87),
                    alignment=alignment.center,
                )
            )
        else:
            self.sent_content_buttons = [ 
                Container( 
                    content=ft.Row( 
                        controls=[ 
                            Checkbox(value=False, visible=False, on_change=lambda e: self.toggle_email_selection(e, email)), 
                            email
                        ],
                        alignment=alignment.center_left
                    ) 
                ) 
                for email in sent_emails
            ] 
            self.load_sent_content.extend(self.sent_content_buttons)

        self.sent_mail_view.content.controls = self.load_sent_content 
        self.page.update()
        self.adjust_content_width()

    def toggle_select_sent(self, e): 
        for sent_mail_button in self.sent_content_buttons: 
            sent_mail_button.content.controls[0].visible = not sent_mail_button.content.controls[0].visible
            sent_mail_button.update() 
        self.select_all_button.visible = not self.select_all_button.visible 
        self.delete_button.visible = not self.delete_button.visible 
        self.page.update()

    def select_all_sent(self, e): 
        select_all_value = not all(email in self.selected_emails for email in self.sent_emails) 
        self.selected_emails = self.sent_emails if select_all_value else [] 
        for sent_mail_button in self.sent_content_buttons: 
            sent_mail_button.content.controls[0].value = select_all_value 
            sent_mail_button.update() 
        self.delete_button.visible = bool(self.selected_emails)
        self.page.update() 
                
    def delete_sent(self, e): 
        self.sent_emails = [email for email in self.sent_emails if email not in self.selected_emails] 
        self.selected_emails = [] 
        self.show_sent_button(None) 
        self.page.update()
   
    def load_sent_button(self, content):
        self.main_content_icon.controls.clear()
        self.back_button = IconButton(icon=icons.CANCEL, on_click=lambda e: self.close_main_content_icon("sent"), icon_size=30)
        self.forward_button = IconButton(icon=icons.FORWARD, on_click=lambda _: self.forward_email(content), icon_size=30) 

        self.email_content_width = self.page.width * 0.5 if self.navigation_rail_expanded else self.page.width * 0.65
        self.sent_content = Container(
            ListView(
                controls=[ 
                    Row(controls=[self.back_button, self.forward_button], alignment=alignment.top_right),
                    Text(value=f"To: {content['To']}"), 
                    Text(value=f"Subject: {content['Subject']}"), 
                    Text(value=content["Body"])
                ],
                spacing=10,
                expand=True
            ),
            alignment=alignment.center_right,
            bgcolor=colors.WHITE,
            shadow=BoxShadow(blur_radius=10, spread_radius=2, color=colors.BLACK12),
            expand=True,
            width=self.email_content_width,
        )

        self.main_content_icon.controls.append(self.sent_content)
        self.page.update()
        self.adjust_content_width()

    def save_outbox_mail(self, e):
        self.save_outbox_content = {
            "To": self.recipient.value,
            "Subject": self.subject.value,
            "Body": self.body.value
        }
        self.display_outbox_content = f"To: {self.recipient.value}\nSubject: {self.subject.value}\nBody: {self.body.value}"
    
        self.outbox_button = Container( 
            content=ft.TextButton( 
                text=self.display_outbox_content, 
                on_click=lambda e, outbox_list=self.save_outbox_content: self.load_outbox_button(outbox_list) 
            ), 
            width=330,
            height=70,
            bgcolor=colors.GREY_100,
            padding=5,
            border_radius=5, 
            alignment=alignment.center_left,
        )
        self.outbox_emails.append(self.outbox_button)
        self.outbox_save_emails.append(self.save_outbox_content)
        self.page.update()
     
    def show_outbox_button(self, e):
        self.main_area.content.controls.clear()
        self.selected_emails = []

        self.delete_button = IconButton(icon=icons.DELETE, on_click=self.delete_outbox, visible=False)
        self.select_button = IconButton(icon=icons.CHECK_BOX, on_click=self.toggle_select_outbox)
        self.search_bar = TextField(hint_text="Search...", width=250, bgcolor=colors.BLACK12, color=colors.BLACK, on_change=self.search_outbox) 
        self.select_all_button = IconButton(icon=icons.CHECK_BOX, on_click=lambda e: self.select_all_outbox(e), visible=False)
    
        self.outbox_controls_row = Container(
            content=Row(
                controls=[
                    self.search_bar,
                    self.select_button,
                ],
                alignment=MainAxisAlignment.SPACE_EVENLY,
                spacing=10
            ),
            border_radius=5,
            shadow=[ft.BoxShadow(color=ft.colors.GREY, blur_radius=2)],
            bgcolor=colors.WHITE,
            padding=2,
            margin=5
        )

        self.load_outbox_content = [self.outbox_controls_row]
        if not self.outbox_emails: 
            self.load_outbox_content.append( 
                Container( 
                    content=Text("Outbox is empty", text_align=TextAlign, color=colors.BLACK87), 
                    alignment=alignment.center,
                    bgcolor=colors.WHITE
                ) 
            )
        else:
            self.update_outbox_content(self.outbox_emails)

        self.outbox_view_width = self.page.width * 0.3

        self.outbox_mail_list = Container( 
            content=ListView( 
                controls=self.load_outbox_content, 
                spacing=10, 
                expand=True
            ), 
            width=self.outbox_view_width, 
            bgcolor=colors.WHITE, 
            height=self.page.height - 60,
            expand=True 
        ) 
        self.outbox_mail_view = Container( 
            content=Column( 
                controls=[ 
                    self.outbox_mail_list, 
                    ft.Row(controls=[self.select_all_button, self.delete_button], 
                    alignment=MainAxisAlignment.SPACE_BETWEEN) 
                ], 
                expand=True 
            ), 
            width=self.outbox_view_width, 
            bgcolor=colors.WHITE, expand=True
        )
        self.main_area.content.controls.append(self.outbox_mail_view)
        self.page.update()
        self.adjust_content_width()

    def search_outbox(self, e):
        outbox_search_query = e.control.value.lower()

        if not outbox_search_query:
            self.update_outbox_content(self.outbox_emails)
            self.page.update() 
            return

        outbox_filtered_emails = [
            outbox_search for outbox_search in self.outbox_save_emails
            if (
                ("Subject" in outbox_search and outbox_search_query in outbox_search['Subject'].lower()) or
                ("To" in outbox_search and outbox_search_query in outbox_search['To'].lower()) or
                ("Body" in outbox_search and outbox_search_query in outbox_search['Body'].lower())
            )
        ]
        outbox_filtered_buttons = [ 
           outbox_ui_element for outbox_ui_element, outbox_data in zip(self.outbox_emails, self.outbox_save_emails) if outbox_data in outbox_filtered_emails 
        ] 
        
        self.update_outbox_content(outbox_filtered_buttons)

    def update_outbox_content(self, outbox_emails):
        self.load_outbox_content = [self.outbox_controls_row]

        if not outbox_emails:
            self.load_outbox_content.append(
                Container(
                    content=Text("No results found", text_align=TextAlign, color=colors.BLACK87),
                    alignment=alignment.center,
                )
            )
        else:
            self.outbox_content_buttons = [ 
                Container( 
                    content=ft.Row( 
                        controls=[ 
                            Checkbox(value=False, visible=False, on_change=lambda e: self.toggle_email_selection(e, email)), 
                            email
                        ],
                        alignment=alignment.center_left
                    ) 
                ) 
                for email in outbox_emails
            ] 
            self.load_outbox_content.extend(self.outbox_content_buttons)

        self.outbox_mail_view.content.controls = self.load_outbox_content 
        self.page.update()
        self.adjust_content_width()

    def toggle_select_outbox(self, e): 
        for outbox_mail_button in self.outbox_content_buttons: 
            outbox_mail_button.content.controls[0].visible = not outbox_mail_button.content.controls[0].visible
            outbox_mail_button.update() 
        self.select_all_button.visible = not self.select_all_button.visible 
        self.delete_button.visible = not self.delete_button.visible 
        self.page.update()

    def select_all_outbox(self, e): 
        select_all_value = not all(email in self.selected_emails for email in self.outbox_emails) 
        self.selected_emails = self.outbox_emails if select_all_value else [] 
        for outbox_mail_button in self.outbox_content_buttons: 
            outbox_mail_button.content.controls[0].value = select_all_value 
            outbox_mail_button.update() 
        self.delete_button.visible = bool(self.selected_emails)
        self.page.update() 
                
    def delete_outbox(self, e):
        self.outbox_emails = [email for email in self.outbox_emails if email not in self.selected_emails]
        self.selected_emails = []
        self.show_outbox_button(None)
        self.page.update()

    def load_outbox_button(self, content):
        self.main_content_icon.controls.clear()
        self.back_button = IconButton(icon=icons.CANCEL, on_click=lambda e: self.close_main_content_icon("outbox"), icon_size=30)
        self.forward_button = IconButton(icon=icons.FORWARD, on_click=lambda _: self.forward_email(content), icon_size=30) 
        
        self.email_content_width = self.page.width * 0.5 if self.navigation_rail_expanded else self.page.width * 0.65
        self.outbox_content = Container(
                content=ListView(
                    controls=[ 
                    Row(controls=[self.back_button, self.forward_button], alignment=alignment.top_right), 
                    Text(value=f"To: {content['To']}"), 
                    Text(value=f"Subject: {content['Subject']}"), 
                    Text(value=content["Body"])
                ],
                spacing=10,
                expand=True
            ),
            alignment=alignment.center_right,
            bgcolor=colors.WHITE,
            shadow=BoxShadow(blur_radius=10, spread_radius=2, color=colors.BLACK12),
            expand=True,
            width=self.email_content_width,
            height=self.page.height
        )
        self.main_content_icon.controls.append(self.outbox_content)
        self.page.update()
        self.adjust_content_width()

    def login(self, e):
        self.page.overlay.clear()
        
        self.login_text = Text("Please login here......", italic=True, size=30)
        self.login_username = TextField(label="Username", hint_text="Enter username")
        self.login_password = TextField(label="Password", password=True, can_reveal_password=True, hint_text="Enter password")
        self.submit_login = ElevatedButton(text="Submit", on_click=lambda e: self.check_login(e))
        self.cancel_login = ElevatedButton(text="Cancel", on_click=lambda e: self.remove_overlay(self.login_page))
        
        self.login_page = Container(
                content=Container(
                    content=Column(
                       controls=[self.login_text, self.login_username, self.login_password, 
                    Row(controls=[self.submit_login, self.cancel_login], alignment=MainAxisAlignment.CENTER)
                    ],
                    alignment=MainAxisAlignment.CENTER,
                    horizontal_alignment=CrossAxisAlignment.CENTER  
                ),
                alignment=alignment.center,  # Center the inner container
                width=self.page.width * 0.4,
                height=self.page.height * 0.4,
                padding=20,
                border_radius=10,
                bgcolor=colors.WHITE,
                shadow=ft.BoxShadow(blur_radius=10, spread_radius=2, color=colors.BLACK87)
            ),
            alignment=alignment.center,
            expand=True    
        )
        self.page.overlay.append(self.login_page)
        self.page.update()

    def check_login(self, e):
        self.remove_overlay(self.login_page)
        self.loading_overlay.show()
        time.sleep(1)
        username = self.login_username.value
        password = self.login_password.value

        conn = sqlite3.connect('ShowMeGrace.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Grace WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            self.loggin = True 
            self.page.overlay.clear() 
            self.init_content()
            self.load_mail_form() 
            Messagebox("Login successful!", self.page)
        else:
            Messagebox("Invalid username or password.", self.page)
        self.loading_overlay.hide()
        self.page.update() 

    def signup(self, e):
        self.page.overlay.clear()
        self.signup_text = Text("Please signup here.......", italic=True, size=30)
        self.name = TextField(label="First and last name", hint_text="Enter first and last name")
        self.signup_username = TextField(label="Username", hint_text="Enter username")
        self.signup_password = TextField(label="Password", password=True, can_reveal_password=True, hint_text="Enter password")
        self.submit_signup = ElevatedButton(text="Submit", on_click=lambda e: self.check_signup(e))
        self.cancel_signup = ElevatedButton(text="Cancel", on_click=lambda e: self.remove_overlay(self.signup_page))

        self.signup_page = Container(
            content=Container(
                content=Column(
                    controls=[
                        self.signup_text, self.name, self.signup_username, self.signup_password, 
                    Row(
                        controls=[self.submit_signup, self.cancel_signup], alignment=ft.MainAxisAlignment.CENTER 
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,  # Center vertically
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER  # Center horizontally   
                ),
                alignment=alignment.center,  # Center the inner container
                width=self.page.width * 0.4,
                height=self.page.height * 0.4,
                padding=20,
                border_radius=10,
                bgcolor=colors.WHITE,
                shadow=ft.BoxShadow(blur_radius=10, spread_radius=2, color=ft.colors.BLACK87)
            ),
            expand=True,
            alignment=alignment.center
        )
        self.page.overlay.append(self.signup_page)
        self.page.update()

    def check_signup(self, e):
        self.remove_overlay(self.signup_page)
        self.loading_overlay.show()
        time.sleep(1)
        username = self.signup_username.value
        password = self.signup_password.value

        if username and password:
            conn = sqlite3.connect('ShowMeGrace.db')
            cursor = conn.cursor()
            try:
                cursor.execute('INSERT INTO Grace (username, password) VALUES (?, ?)', (username, password))
                conn.commit()
                Messagebox("Signup successful!", self.page)
                self.login(e)
            except sqlite3.IntegrityError:
                Messagebox("Username already exists!", self.page)
            finally:
                conn.close()
        else:
            Messagebox("Please enter both username and password.", self.page)
        self.loading_overlay.hide()
        self.page.update()

    def mail_limits(self, plan, e):
        self.plan = plan
        self.email_count = 0
        self.limit = self.get_limit()

    def get_limit(self):
        if self.plan == 'basic':
            return 50
        elif self.plan == 'standard':
            return 100
        elif self.plan == 'advanced':
            return 150
        elif self.plan == 'free':
            return 10
        else:
            raise ValueError("Invalid plan")
        
if __name__ == "__main__":
    ft.app(target=Startup)
