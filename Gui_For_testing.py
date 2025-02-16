
import sys
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QFileDialog, QMessageBox, QTableView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

class ThrustTestingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Static Thrust Testing")
        self.setGeometry(100, 100, 1000, 600)
        self.data = None  # Initialize data to None; will hold the CSV data after loading
        self.current_unit = 'ozf'  # Default unit is ounces-force (ozf)

        # Main layout setup
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)

        # Left panel: Plot and max thrust display
        self.plot_canvas = FigureCanvas(Figure(figsize=(5, 4)))  # Canvas for matplotlib plot
        self.ax = self.plot_canvas.figure.add_subplot(111)  # Create plot axes

        # Create a vertical layout for the plot area
        plot_layout = QVBoxLayout()

        # Create the navigation toolbar
        self.toolbar = NavigationToolbar(self.plot_canvas, self)
        self.toolbar.setStyleSheet("""
            QToolBar {
                background: white;
                border: none;
            }
            QToolButton {
                background: white;
                border: none;
            }
            QToolButton:hover {
                background: #f0f0f0;
            }
        """)

        # Add both the toolbar and canvas to the plot layout
        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.plot_canvas)

        # Create a widget to hold the plot layout
        plot_widget = QWidget()
        plot_widget.setLayout(plot_layout)

        # Add the plot widget to the main layout
        main_layout.addWidget(plot_widget)

        # Right panel: Controls and metrics
        side_panel = QVBoxLayout()

        # Button to load a CSV file
        self.load_button = QPushButton("Load CSV")
        self.load_button.clicked.connect(self.load_csv)  # Connect button to file loader function
        side_panel.addWidget(self.load_button)

        # Max thrust display title
        self.max_label_title = QLabel("Maximum Thrust:")
        self.max_label_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        side_panel.addWidget(self.max_label_title)

        # Dynamic label to display the maximum thrust value
        self.max_label = QLabel("")
        side_panel.addWidget(self.max_label)

        # Button to toggle between ozf and lbf
        self.toggle_units_button = QPushButton("Toggle Units (ozf / lbf)")
        self.toggle_units_button.clicked.connect(self.toggle_units)  # Connect to toggle function
        side_panel.addWidget(self.toggle_units_button)

        # Section to calculate average thrust between two time points
        self.avg_calc_label = QLabel("Calculate Average Thrust:")
        self.avg_calc_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        side_panel.addWidget(self.avg_calc_label)

        # Input fields for start and end times
        hbox_avg_range = QHBoxLayout()
        self.start_time_input = QLineEdit(self)
        self.start_time_input.setPlaceholderText("Start Time")
        self.start_time_input.setFixedWidth(100)
        hbox_avg_range.addWidget(self.start_time_input)

        self.end_time_input = QLineEdit(self)
        self.end_time_input.setPlaceholderText("End Time")
        self.end_time_input.setFixedWidth(100)
        hbox_avg_range.addWidget(self.end_time_input)

        # Add the time range input to the side panel
        side_panel.addLayout(hbox_avg_range)

        # Button to calculate the average thrust
        self.calc_avg_button = QPushButton("Calculate Average")
        self.calc_avg_button.clicked.connect(self.calculate_average)  # Connect to average calculation
        side_panel.addWidget(self.calc_avg_button)

        # Label to display the result of the average calculation
        self.avg_result_label = QLabel("")
        side_panel.addWidget(self.avg_result_label)

        # Button to view the loaded data as a DataFrame
        self.view_dataframe_button = QPushButton("View DataFrame")
        self.view_dataframe_button.clicked.connect(self.show_dataframe)  # Connect to DataFrame viewer
        side_panel.addWidget(self.view_dataframe_button)

        side_panel.addStretch()  # Add stretch to push components to the top
        main_layout.addLayout(side_panel)

    def toggle_units(self):
        """
        Toggle the units between ozf and lbf for thrust values.
        Update the plot and maximum thrust label accordingly.
        """
        if self.data is None:
            QMessageBox.warning(self, "Warning", "Please load a CSV file first!")
            return

        # Check the current unit and switch to the other
        if self.current_unit == 'ozf':
            # Convert to lbf
            self.current_unit = 'lbf'
            self.data['thrust_converted'] = self.data['thrust'] / 16  # 1 lbf = 16 ozf
            y_label = "Thrust (lbf)"
        else:
            # Switch back to ozf
            self.current_unit = 'ozf'
            self.data['thrust_converted'] = self.data['thrust']  # Use original values in ozf
            y_label = "Thrust (ozf)"

        # Update the plot with converted data
        self.ax.clear()
        self.ax.plot(self.data['time'], self.data['thrust_converted'],
                     label=f"Thrust vs Time ({self.current_unit.upper()})")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel(y_label)  # Update the y-axis label
        self.ax.legend()
        self.plot_canvas.draw()

        # Update the maximum thrust display
        max_thrust_converted = self.data['thrust_converted'].max()
        self.max_label.setText(f"{max_thrust_converted:.2f} {self.current_unit}")

    def load_csv(self):
        """
        Load a CSV file and display the initial plot in the default unit (ozf).
        """
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv)", options=options)
        if not file_path:
            return

        try:
            # Read the CSV file into a pandas DataFrame
            self.data = pd.read_csv(file_path)

            # Ensure the required columns are present
            self.data.rename(columns={'Time (s)': 'time', 'Thrust (ozf)': 'thrust'}, inplace=True)
            if 'time' not in self.data.columns or 'thrust' not in self.data.columns:
                QMessageBox.critical(self, "Error", "CSV must contain 'time' and 'thrust' columns!")
                return

            # Copy the thrust column to a new column for conversion (starts as ozf)
            self.data['thrust_converted'] = self.data['thrust']

            # Plot the time vs thrust data (default: ozf)
            self.ax.clear()
            self.ax.plot(self.data['time'], self.data['thrust_converted'], label="Thrust vs Time (ozf)")
            self.ax.set_xlabel("Time (s)")
            self.ax.set_ylabel("Thrust (ozf)")  # Default label
            self.ax.legend()
            self.plot_canvas.draw()

            # Display the maximum thrust in ozf
            max_thrust = self.data['thrust'].max()
            self.max_label.setText(f"{max_thrust:.2f} ozf")

        except Exception as e:
            # Handle errors in loading and processing the file
            QMessageBox.critical(self, "Error", f"Failed to load CSV: {str(e)}")

    def calculate_average(self):
        """Calculate the average thrust between two time points."""
        if self.data is None:
            QMessageBox.warning(self, "Warning", "Please load a CSV file first!")
            return

        try:
            start_time = float(self.start_time_input.text())
            end_time = float(self.end_time_input.text())

            if start_time >= end_time:
                QMessageBox.warning(self, "Warning", "Start time must be less than end time!")
                return

            # Filter data within the time range
            mask = (self.data['time'] >= start_time) & (self.data['time'] <= end_time)
            avg_thrust = self.data.loc[mask, 'thrust'].mean()

            if np.isnan(avg_thrust):
                self.avg_result_label.setText("No data in range!")
            else:
                self.avg_result_label.setText(f"Average Thrust: {avg_thrust:.2f} N")
        except ValueError:
            QMessageBox.warning(self, "Warning", "Please enter valid numbers for the time range.")

    def show_dataframe(self):
        """Display the DataFrame in a table view."""
        if self.data is None:
            QMessageBox.warning(self, "Warning", "Please load a CSV file first!")
            return

        # Create a new window for the DataFrame
        df_window = QWidget()
        df_window.setWindowTitle("DataFrame Viewer")
        df_window.setGeometry(150, 150, 800, 600)

        layout = QVBoxLayout()
        df_window.setLayout(layout)

        table = QTableView()
        model = QStandardItemModel()

        # Populate the view
        model.setHorizontalHeaderLabels(self.data.columns.tolist())
        for row in self.data.itertuples(index=False):
            items = [QStandardItem(str(item)) for item in row]
            model.appendRow(items)

        table.setModel(model)
        layout.addWidget(table)

        df_window.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ThrustTestingApp()
    window.show()
    sys.exit(app.exec_())