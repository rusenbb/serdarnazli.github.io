from flask import Flask, render_template, request, jsonify
import io
import base64
import matplotlib
matplotlib.use('Agg')  # Use Agg backend to avoid GUI errors
import matplotlib.pyplot as plt
from scipy.stats import t
import numpy as np

app = Flask(__name__)

def calculate_class_stats(components):
    total_weight = sum(comp['weight'] for comp in components.values())  # Ensure total weight is accounted for
    class_average = sum(comp['average'] * (comp['weight'] / total_weight) for comp in components.values())
    class_variance = sum((comp['stdDev'] ** 2) * ((comp['weight'] / total_weight) ** 2) for comp in components.values())
    class_std_dev = class_variance ** 0.5
    return class_average, class_std_dev

def calculate_student_percentile(student_scores, components, class_average, class_std_dev, sample_size):
    total_weight = sum(components[comp]['weight'] for comp in components)
    student_final_score = sum(student_scores[comp] * (components[comp]['weight'] / total_weight) for comp in student_scores)
    degrees_of_freedom = sample_size - 1
    percentile = t.cdf(student_final_score, df=degrees_of_freedom, loc=class_average, scale=class_std_dev)
    return percentile

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/', methods=['POST'])
def calculate():
    data = request.get_json()
    print("Received data:", data)  # Debug print

    components = data['components']
    student_scores = data['studentScores']

    try:
        class_avg, class_std_dev = calculate_class_stats(components)
        percentile = calculate_student_percentile(student_scores, components, class_avg, class_std_dev, sample_size=35)

        # Plotting
        fig, ax = plt.subplots()
        x = np.linspace(0, 100, 1000)
        y = t.pdf(x, df=34, loc=class_avg, scale=class_std_dev)
        ax.plot(x, y, label='Class Distribution')

        weighted_student_score = sum(student_scores[comp] * (components[comp]['weight'] / 100) for comp in student_scores)
        ax.axvline(x=weighted_student_score, color='r', linestyle='--', label='Student Score')
        
        ax.set_xlim(0, 100)
        ax.set_ylim(bottom=0)
        ax.legend()
        # Convert plot to PNG image
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        
        return jsonify({'plot_url': plot_url, 'percentile': percentile})
    except KeyError as e:
        print("KeyError:", e)
        return jsonify({'error': f"KeyError: {e}"})


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
