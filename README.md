# Intelligent Ambulance Allocation System

An AI-assisted ambulance allocation and simulated live-tracking system developed for Islamabad as a BSCS AI semester project.

## Project Overview

The system uses machine learning to predict ambulance response time and assist in selecting the most suitable available ambulance for an emergency request.

The project pipeline is:

Data → Preprocessing → KNN + ANN + Random Forest → Model Comparison → AI Allocation → Dynamic Tracking Dashboard

## Features

- Synthetic emergency-response dataset for prototype development
- Data preprocessing and feature engineering
- KNN regression
- Artificial Neural Network (ANN) regression
- Random Forest regression
- Train/validation/test evaluation
- MAE, RMSE, and R² performance metrics
- AI-based ambulance allocation
- Nearest-ambulance baseline
- Interactive Islamabad map
- Simulated live ambulance movement
- Countdown timer and predicted ETA
- Ambulance fleet availability display
- Gradio-based emergency dispatch dashboard

## Machine Learning Models

Three machine learning approaches are compared:

- K-Nearest Neighbors (KNN)
- Artificial Neural Network (ANN)
- Random Forest

The models are evaluated using the same held-out test data. The model with the lowest validation RMSE is selected for the response-time prediction component.

## Dataset

The project uses a synthetically generated emergency dataset designed for prototype development.

The dataset should not be considered real Islamabad ambulance records.

The synthetic data allows the system to demonstrate ambulance allocation, response-time prediction, and emergency dispatch functionality without using private or unavailable real-world ambulance records.

## Tracking

The ambulance tracking component is simulated for academic demonstration.

The system displays ambulance movement, journey progress, remaining distance, and estimated arrival time on an Islamabad-based interactive map.

A real-world deployment would replace the simulated coordinates with live GPS data from ambulance devices.

## Application

The final application provides an emergency dispatch dashboard where the user can enter:

- Emergency location
- Emergency type
- Severity
- Traffic level
- Weather conditions

The system then provides an AI-assisted ambulance allocation decision, predicted ETA, distance, fleet status, and simulated live tracking.

## Technologies Used

- Python
- Google Colab
- Pandas
- NumPy
- Scikit-learn
- Matplotlib
- Seaborn
- Folium
- Gradio
- Joblib

## Project Files

- `project final.ipynb` — Complete Google Colab notebook containing the project workflow
- `Ambulance_Allocation_System_Final_Complete.py` — Final Gradio application

## How to Run

1. Open `project final.ipynb` in Google Colab.
2. Run the notebook cells from top to bottom.
3. Install the required Python libraries when prompted.
4. Run the application cell to launch the Gradio dashboard.
5. Use the emergency request form to test ambulance allocation and simulated tracking.

## Important Note

This project is an academic prototype. The dataset and ambulance movement are simulated and are not intended for real emergency-service deployment.

A production system would require verified ambulance GPS data, real-time traffic and routing services, live emergency-service integration, and extensive validation.
