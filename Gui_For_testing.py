
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


class ThrustTestingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Static Thrust Testing")
        self.setGeometry(100, 100, 1000, 600)
        self.data = None

        # Main layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)

        # Left: Plot and max value
        self.plot_canvas = FigureCanvas(Figure(figsize=(5, 4)))
        self.ax = self.plot_canvas.figure.add_subplot(111)
        main_layout.addWidget(self.plot_canvas)

        # Right: File loader, max thrust, and average calculation
        side_panel = QVBoxLayout()

        # Load CSV Button
        self.load_button = QPushButton("Load CSV")
        self.load_button.clicked.connect(self.load_csv)
        side_panel.addWidget(self.load_button)

        # Max Value
        self.max_label_title = QLabel("Maximum Thrust:")
        self.max_label_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        side_panel.addWidget(self.max_label_title)

        self.max_label = QLabel("")
        side_panel.addWidget(self.max_label)

        # Time range input for average calculation
        self.avg_calc_label = QLabel("Calculate Average Thrust:")
        self.avg_calc_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        side_panel.addWidget(self.avg_calc_label)

        hbox_avg_range = QHBoxLayout()
        self.start_time_input = QLineEdit(self)
        self.start_time_input.setPlaceholderText("Start Time")
        self.start_time_input.setFixedWidth(100)
        hbox_avg_range.addWidget(self.start_time_input)

        self.end_time_input = QLineEdit(self)
        self.end_time_input.setPlaceholderText("End Time")
        self.end_time_input.setFixedWidth(100)
        hbox_avg_range.addWidget(self.end_time_input)

        side_panel.addLayout(hbox_avg_range)

        self.calc_avg_button = QPushButton("Calculate Average")
        self.calc_avg_button.clicked.connect(self.calculate_average)
        side_panel.addWidget(self.calc_avg_button)

        self.avg_result_label = QLabel("")
        side_panel.addWidget(self.avg_result_label)

        # Button to show data frame
        self.view_dataframe_button = QPushButton("View DataFrame")
        self.view_dataframe_button.clicked.connect(self.show_dataframe)
        side_panel.addWidget(self.view_dataframe_button)

        side_panel.addStretch()
        main_layout.addLayout(side_panel)

    def load_csv(self):
        """Load a CSV file and display its time vs thrust plot."""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv)", options=options)
        if not file_path:
            return

        try:

            self.data = pd.read_csv(file_path)
            self.data.rename(columns={'Time (s)': 'time', 'Thrust (ozf)': 'thrust'}, inplace=True)

            if 'time' not in self.data.columns or 'thrust' not in self.data.columns:
                QMessageBox.critical(self, "Error", "CSV must contain 'time' and 'thrust' columns!")
                return

            # Plot
            self.ax.clear()
            self.ax.plot(self.data['time'], self.data['thrust'], label="Thrust vs Time")
            self.ax.set_xlabel("Time (s)")
            self.ax.set_ylabel("Thrust (ozf)")
            self.ax.legend()
            self.plot_canvas.draw()

            # Max Thrust
            max_thrust = self.data['thrust'].max()
            self.max_label.setText(f"{max_thrust:.2f} N")
        except Exception as e:
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