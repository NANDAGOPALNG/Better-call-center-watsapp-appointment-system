# 10-Step Demo Flow

1. Open the dashboard and show all five analytics cards.
2. Open **New Appointment** from the navigation bar.
3. Enter a customer name, E.164 phone number, future time, and purpose.
4. Submit the form and show the success toast.
5. Show the new row, including purpose, AI summary, status, and reminder state.
6. Verify the customer's WhatsApp Sandbox confirmation, or demonstrate the
   Supabase `message_logs` row while using mock mode.
7. Change the row from **Scheduled** to **Confirmed** and show the live toast.
8. Create or adjust an appointment to occur within the next hour.
9. After the reminder job runs, show the WhatsApp message and the row changing to
   **Reminder Sent** with reminder state **Sent**.
10. Mark the appointment **Completed** or **Cancelled**, then show the refreshed
    dashboard analytics and `/api/health` response.
