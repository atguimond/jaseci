from django.core import mail
from jaseci.svcs.mail.mail_svc import mail_svc as ms, emailer as em
from jaseci_serv.jaseci_serv.settings import EMAIL_CONFIG

#################################################
#                 EMAIL APP ORM                 #
#################################################


class mail_svc(ms):
    def connect(self, configs):
        user = configs.get("user")
        backend = configs.get("backend", "smtp")
        sender = configs.get("sender", user)

        server = mail.get_connection(
            backend=f"django.core.mail.backends.{backend}.EmailBackend",
            host=configs.get("host"),
            port=configs.get("port"),
            username=user,
            password=configs.get("pass"),
            use_tls=configs.get("tls"),
        )
        return emailer(server, sender, configs["templates"])

    def get_config(self, hook) -> dict:
        return hook.build_config("EMAIL_CONFIG", EMAIL_CONFIG)


# ----------------------------------------------- #


####################################################
#                   EMAIL CONFIG                   #
####################################################


class emailer(em):
    def __init__(self, server, sender, templates):
        super().__init__(server, sender)

        self.activ_subj = templates["activation_subj"]
        self.activ_body = templates["activation_body"]
        if "{{code}}" not in self.activ_body and "{{link}}" not in self.activ_body:
            raise Exception("{{code/link}} must be present in email template")

        self.activ_html = templates["activation_html_body"]
        if "{{code}}" not in self.activ_html and "{{link}}" not in self.activ_html:
            raise Exception("{{code/link}} must be present in email template")

        self.reset_subj = templates["resetpass_subj"]
        self.reset_body = templates["resetpass_body"]
        if "{{token}}" not in self.reset_body:
            raise Exception("{{token}} must be present in email template")

        self.reset_html = templates["resetpass_html_body"]
        if "{{token}}" not in self.reset_html:
            raise Exception("{{token}} must be present in email template")

    def send_activation_email(self, email, code, link):
        """Apply relevant parameters to loaded templates"""
        body = self.activ_body.replace("{{code}}", code).replace("{{link}}", link)
        html = self.activ_html.replace("{{code}}", code).replace("{{link}}", link)

        msg = mail.EmailMultiAlternatives(
            subject=self.activ_subj,
            body=body,
            from_email=self.sender,
            to=[email],
            connection=self.server,
        )

        msg.attach_alternative(html, "text/html")
        msg.send(fail_silently=False)

    def send_reset_email(self, email, token):
        """Apply relevant parameters to loaded templates"""
        body = self.reset_body.replace("{{token}}", token)
        html = self.reset_html.replace("{{token}}", token)

        msg = mail.EmailMultiAlternatives(
            subject=self.reset_subj,
            body=body,
            from_email=self.sender,
            to=[email],
            connection=self.server,
        )
        msg.attach_alternative(html, "text/html")
        msg.send(fail_silently=False)

    def send_custom_email(
        self,
        sender: str = None,
        recipients: list = [],
        subject: str = "Jaseci Email",
        body: tuple = ("", ""),
    ):
        msg = mail.EmailMultiAlternatives(
            subject=subject,
            body=body[0],
            from_email=self.sender if sender is None else sender,
            to=recipients,
            connection=self.server,
        )
        msg.attach_alternative(body[1], "text/html")
        msg.send(fail_silently=False)

    def terminate(self):
        self.server.close()
