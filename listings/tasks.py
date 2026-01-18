from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Payment

@shared_task
def send_payment_confirmation_email(to_email, booking_id, amount, tx_ref):
    """
    Send payment confirmation email to the guest.
    
    Args:
        to_email (str): Email address of the recipient
        booking_id (int): Booking ID
        amount (str): Payment amount
        tx_ref (str): Transaction reference
    """
    subject = f"Payment Confirmation - Booking #{booking_id}"
    
    message = f"""
    Hello,
    
    Your payment has been successfully processed!
    
    Booking Details:
    - Booking ID: {booking_id}
    - Amount: {amount}
    - Transaction Reference: {tx_ref}
    - Status: Completed
    
    Thank you for booking with us. We look forward to hosting you!
    
    Best regards,
    ALX Travel App Team
    """
    
    html_message = f"""
    <html>
      <body style="font-family: Arial, sans-serif;">
        <h2>Payment Confirmation</h2>
        <p>Hello,</p>
        <p>Your payment has been successfully processed!</p>
        <h3>Booking Details:</h3>
        <ul>
          <li><strong>Booking ID:</strong> {booking_id}</li>
          <li><strong>Amount:</strong> {amount}</li>
          <li><strong>Transaction Reference:</strong> <code>{tx_ref}</code></li>
          <li><strong>Status:</strong> Completed</li>
        </ul>
        <p>Thank you for booking with us. We look forward to hosting you!</p>
        <p>Best regards,<br/>ALX Travel App Team</p>
      </body>
    </html>
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            html_message=html_message,
            fail_silently=False,
        )
        return f"Email sent successfully to {to_email}"
    except Exception as e:
        return f"Failed to send email: {str(e)}"

@shared_task
def send_booking_confirmation_email(to_email, booking_id, listing_title, start_date, end_date):
    """
    Send booking confirmation email to the guest.
    
    Args:
        to_email (str): Email address of the recipient
        booking_id (int): Booking ID
        listing_title (str): Title of the listing
        start_date (str): Start date of booking
        end_date (str): End date of booking
    """
    subject = f"Booking Confirmation - {listing_title}"
    
    message = f"""
    Hello,
    
    Your booking has been confirmed!
    
    Booking Details:
    - Booking ID: {booking_id}
    - Property: {listing_title}
    - Check-in: {start_date}
    - Check-out: {end_date}
    
    Please proceed to payment to complete your reservation.
    
    Best regards,
    ALX Travel App Team
    """
    
    html_message = f"""
    <html>
      <body style="font-family: Arial, sans-serif;">
        <h2>Booking Confirmation</h2>
        <p>Hello,</p>
        <p>Your booking has been confirmed!</p>
        <h3>Booking Details:</h3>
        <ul>
          <li><strong>Booking ID:</strong> {booking_id}</li>
          <li><strong>Property:</strong> {listing_title}</li>
          <li><strong>Check-in:</strong> {start_date}</li>
          <li><strong>Check-out:</strong> {end_date}</li>
        </ul>
        <p>Please proceed to payment to complete your reservation.</p>
        <p>Best regards,<br/>ALX Travel App Team</p>
      </body>
    </html>
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            html_message=html_message,
            fail_silently=False,
        )
        return f"Booking confirmation email sent to {to_email}"
    except Exception as e:
        return f"Failed to send booking confirmation: {str(e)}"
