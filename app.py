import streamlit as st
import csv
import pandas as pd
import os
from datetime import datetime
from fpdf import FPDF
import io

# Define violation types and fines
violations = {
    "Red Light Violation": 500,
    "No Seatbelt": 1000,
    "Illegal Parking": 2000,
    "Driving Without Licence": 5000,
    "Speeding": 500,
    "Driving Without Helmet": 1000
}

filename = "Violations.csv"

# Initialize CSV with an 'id' column if not present
if not os.path.exists(filename):
    with open(filename, "w", newline="") as file:
        fieldnames = ["id", "license_plate", "violation_type", "fine", "timestamp"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

# Helper: Get next unique ID
def get_next_id():
    try:
        df = pd.read_csv(filename)
        if df.empty or "id" not in df.columns:
            return 1
        else:
            return int(df["id"].max()) + 1
    except Exception:
        return 1

# Log a Traffic Violation
def log_violation():
    st.header("Log a Traffic Violation")
    
    l_plate = st.text_input("Enter the license plate number:")
    v_type = st.selectbox("Select the violation type:", list(violations.keys()))
    date_input = st.date_input("Enter violation date", datetime.today())
    
    if st.button("Log Violation"):
        fine = violations[v_type]
        violation_id = get_next_id()
        # Append to CSV
        with open(filename, "a", newline="") as file:
            fieldnames = ["id", "license_plate", "violation_type", "fine", "timestamp"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writerow({
                "id": violation_id,
                "license_plate": l_plate,
                "violation_type": v_type,
                "fine": fine,
                "timestamp": date_input.strftime("%Y-%m-%d")
            })
        st.success(f"Violation logged successfully! Fine amount: Rs.{fine}")

# View Violation Records
def view_violations():
    st.header("View Violation Records")
    try:
        df = pd.read_csv(filename)
        st.dataframe(df)
    except Exception as e:
        st.error("Error reading file: " + str(e))

# Search Driver/Vehicle History
def search_history():
    st.header("Search Driver/Vehicle History")
    l_plate = st.text_input("Enter the license plate to search:")
    if st.button("Search"):
        try:
            df = pd.read_csv(filename)
            data = df[df["license_plate"] == l_plate]
            if data.empty:
                st.info("No records found for the given license plate.")
            else:
                st.dataframe(data)
        except Exception as e:
            st.error("Error reading file: " + str(e))

# Analyze Trends
def analyze_trends():
    st.header("Analyze Trends")
    try:
        df = pd.read_csv(filename)
        if df.empty:
            st.info("No violations recorded.")
            return
        
        st.subheader("Most Common Violations:")
        st.write(df["violation_type"].value_counts())
        
        st.subheader("Peak Violation Hours:")
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors='coerce')
        df["hour"] = df["timestamp"].dt.hour
        st.write(df["hour"].value_counts().sort_index())
        
        st.subheader("Total Fine Collected:")
        st.write("₹ " + str(df["fine"].sum()))
    except Exception as e:
        st.error("Error analyzing trends: " + str(e))

# Update or Delete Violation Records
def update_delete_violation():
    st.header("Update or Delete Violation Records")
    try:
        df = pd.read_csv(filename)
        st.dataframe(df)
    except Exception as e:
        st.error("Error reading file: " + str(e))
        return

    v_id = st.number_input("Enter violation ID to update/delete:", min_value=1, step=1)
    action = st.radio("Select action:", ('Update', 'Delete'))
    
    if action == 'Update':
        new_fine = st.number_input("Enter new fine amount:", min_value=0, step=100)
        if st.button("Update Violation"):
            if v_id not in df["id"].values:
                st.error("Violation ID not found.")
                return
            df.loc[df["id"] == v_id, "fine"] = new_fine
            df.to_csv(filename, index=False)
            st.success("Violation updated successfully!")
    elif action == 'Delete':
        if st.button("Delete Violation"):
            if v_id not in df["id"].values:
                st.error("Violation ID not found.")
                return
            df = df[df["id"] != v_id]
            df.to_csv(filename, index=False)
            st.success("Violation deleted successfully!")

# Helper: Create a PDF report from DataFrame using FPDF
def create_pdf(df):
    from fpdf import FPDF

    class PDF(FPDF):
        def header(self):
            self.set_font("Arial", "B", 16)
            self.set_text_color(40, 40, 40)
            self.cell(0, 10, "Traffic Violation Report", border=False, ln=True, align="C")
            self.ln(10)

        def footer(self):
            self.set_y(-15)
            self.set_font("Arial", "I", 8)
            self.set_text_color(100, 100, 100)
            self.cell(0, 10, f"Page {self.page_no()}", align="C")

    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=10)

    # Define styling
    col_widths = [25, 40, 50, 20, 40]  # Adjust column widths to fit content
    headers = df.columns.tolist()
    row_height = 8

    # Header row
    pdf.set_fill_color(200, 200, 200)
    pdf.set_text_color(0)
    pdf.set_font("Arial", style='B', size=10)
    for i, header in enumerate(headers):
        width = col_widths[i] if i < len(col_widths) else 30
        pdf.cell(width, row_height, str(header), border=1, fill=True, align='C')
    pdf.ln(row_height)
    pdf.set_font("Arial", size=10)  # Reset font to normal

    # Rows with alternating fill
    fill = False
    for _, row in df.iterrows():
        pdf.set_fill_color(245, 245, 245) if fill else pdf.set_fill_color(255, 255, 255)
        for i, item in enumerate(row):
            width = col_widths[i] if i < len(col_widths) else 30
            pdf.cell(width, row_height, str(item), border=1, fill=True)
        pdf.ln(row_height)
        fill = not fill

    # Output PDF as bytes
    return pdf.output(dest="S").encode("latin-1")

# Generate Reports (CSV & PDF)
def generate_reports():
    st.header("Generate Reports")
    try:
        df = pd.read_csv(filename)
    except Exception as e:
        st.error("Error reading file: " + str(e))
        return

    st.subheader("Export CSV Report")
    export_filename = st.text_input("Enter CSV filename to export (must end with .csv):", "Report.csv", key="csv")
    if st.button("Export CSV", key="export_csv"):
        try:
            df.to_csv(export_filename, index=False)
            st.success("CSV Report exported successfully!")
            st.download_button(
                label="Download CSV",
                data=df.to_csv(index=False).encode('utf-8'),
                file_name=export_filename,
                mime="text/csv"
            )
        except Exception as e:
            st.error("Error exporting CSV report: " + str(e))
    
    st.subheader("Export PDF Report")
    pdf_filename = st.text_input("Enter PDF filename to export (must end with .pdf):", "Report.pdf", key="pdf")
    if st.button("Export PDF", key="export_pdf"):
        try:
            pdf_bytes = create_pdf(df)
            st.success("PDF Report generated successfully!")
            st.download_button(
                label="Download PDF",
                data=pdf_bytes,
                file_name=pdf_filename,
                mime="application/pdf"
            )
        except Exception as e:
            st.error("Error exporting PDF report: " + str(e))

# Main function to run the Streamlit app with a sidebar menu
def main():
    st.title("Traffic Violation Tracker")
    st.sidebar.title("Menu")
    
    menu_options = [
        "Log Violation",
        "View Violations",
        "Search History",
        "Analyze Trends",
        "Update/Delete Violation",
        "Generate Reports"
    ]
    choice = st.sidebar.selectbox("Select an option", menu_options)
    
    if choice == "Log Violation":
        log_violation()
    elif choice == "View Violations":
        view_violations()
    elif choice == "Search History":
        search_history()
    elif choice == "Analyze Trends":
        analyze_trends()
    elif choice == "Update/Delete Violation":
        update_delete_violation()
    elif choice == "Generate Reports":
        generate_reports()
    
    st.sidebar.markdown("---")
    st.sidebar.info("Traffic Violation Tracker App")

if __name__ == "__main__":
    main()
