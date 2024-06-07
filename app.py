from flask import Flask, render_template, request, send_file
import pandas as pd
from datetime import datetime, timedelta
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    employee_name = request.form['employee_name']
    clock_in_times = request.form.getlist('clock_in')
    clock_out_times = request.form.getlist('clock_out')
    hourly_rate = float(request.form['hourly_rate'])

    total_hours = 0
    daily_hours = []
    days = ['Monday', 'Wednesday', 'Friday', 'Saturday', 'Sunday']

    for in_time, out_time in zip(clock_in_times, clock_out_times):
        if in_time and out_time:
            in_hours, in_minutes = map(int, in_time.split(':'))
            out_hours, out_minutes = map(int, out_time.split(':'))
            in_time = timedelta(hours=in_hours, minutes=in_minutes)
            out_time = timedelta(hours=out_hours, minutes=out_minutes)

            # Adjust out_time for overnight shift
            if out_time < in_time:
                out_time += timedelta(days=1)

            hours_worked = (out_time - in_time).total_seconds() / 3600
            if hours_worked < 0:
                hours_worked = 0
            daily_hours.append(hours_worked)
            total_hours += hours_worked
        else:
            daily_hours.append(0)

    total_earnings = total_hours * hourly_rate

    # Prepare data for the spreadsheet
    data = {
        'Day': days,
        'Clock In': clock_in_times,
        'Clock Out': clock_out_times,
        'Hours Worked': daily_hours
    }
    df = pd.DataFrame(data)
    df.loc[len(df.index)] = ['Total', '', '', total_hours]

    # Create the spreadsheet
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"weekly_hours_{timestamp}.xlsx"
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # Write the main data
        df.to_excel(writer, index=False, sheet_name='Weekly Data', startrow=2)
        worksheet = writer.sheets['Weekly Data']
        worksheet.cell(row=1, column=1, value=f'Employee Name: {employee_name}')
        worksheet.cell(row=2, column=1, value=f'Total Wages: ${total_earnings}')

    return render_template('result.html', total_hours=total_hours, total_earnings=total_earnings, filename=filename)

@app.route('/download/<filename>')
def download(filename):
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
