class EmailService:
    def __init__(self):
        pass
    
    def send_otp_email(self, user_email: str, user_name: str, otp_code: str, action_type: str):
        """
        Simulate OTP email sending (for demo purposes)
        In production, integrate with actual email service
        """
        print("=" * 60)
        print("🎯 OTP VERIFICATION REQUIRED")
        print("=" * 60)
        print(f"👤 User: {user_name}")
        print(f"📧 Email: {user_email}")
        print(f"🔐 Action: {action_type.upper()} booking")
        print(f"🔢 OTP Code: {otp_code}")
        print(f"⏰ Valid for: 10 minutes")
        print("=" * 60)
        print("💡 In production, this OTP would be sent via:")
        print("   - Email to user's registered email address")
        print("   - SMS to user's mobile number")
        print("   - Push notification to mobile app")
        print("=" * 60)
        
        return True
    
    def send_sms_otp(self, phone_number: str, otp_code: str, action_type: str):
        """
        Simulate SMS OTP sending
        """
        print(f"📱 SMS OTP: {otp_code} sent to {phone_number} for {action_type}")
        return True

# Global instance
email_service = EmailService()