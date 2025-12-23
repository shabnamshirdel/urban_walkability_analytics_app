from flask import Flask, render_template_string, jsonify
import geopandas as gpd
import pandas as pd
import json
import webbrowser
import threading
import os
import numpy as np

app = Flask(__name__)

# Global variables to store data
geojson_response_cache = None
center_coords = [0, 0]

def load_and_optimize_data():
    global geojson_response_cache, center_coords
    
    shapefile_path = "./data/GCWI_SCORE_streetswithsidewalk_Cleaned.shp"
    csv_path = "./data/street_segment_slope.csv"
    
    try:
        # 1. Load Data
        gdf = gpd.read_file(shapefile_path)
        slope_df = pd.read_csv(csv_path)
        
        # 2. Merge Data
        gdf = gdf.merge(slope_df[['ID_TRC', 'slope_normalized']], on='ID_TRC', how='left')
        
        # 3. CRS Conversion
        if gdf.crs != 'EPSG:4326':
            gdf = gdf.to_crs('EPSG:4326')
            
        # 4. Calculate Center
        center_lat = gdf.geometry.centroid.y.mean()
        center_lon = gdf.geometry.centroid.x.mean()
        center_coords = [center_lat, center_lon]

        # 5. Simplify Geometry
        gdf['geometry'] = gdf.geometry.simplify(tolerance=0.00005, preserve_topology=True)

        # 6. Cache JSON
        json_str = gdf.to_json()
        geojson_response_cache = json.loads(json_str)
        
        print(f"Data loaded! {len(gdf)} segments ready.")
        
    except Exception as e:
        print(f"Error loading data: {e}")
        geojson_response_cache = {"type": "FeatureCollection", "features": []}

# Enhanced HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Urban Walkability Analytics</title>
    
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    
    <style>
        :root {
            --primary-gradient: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
            --accent-gradient: linear-gradient(135deg, #ec4899 0%, #f97316 100%);
            --success-gradient: linear-gradient(135deg, #10b981 0%, #3b82f6 100%);
            --text-dark: #0f172a;
            --text-mid: #334155;
            --text-light: #64748b;
            --bg-glass: rgba(255, 255, 255, 0.85);
            --bg-glass-dark: rgba(255, 255, 255, 0.95);
            --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.08);
            --shadow-md: 0 8px 30px rgba(37, 99, 235, 0.15);
            --shadow-lg: 0 20px 60px rgba(37, 99, 235, 0.2);
        }

        * { box-sizing: border-box; }
        
        body { 
            margin: 0; 
            padding: 0; 
            font-family: 'Inter', sans-serif; 
            overflow: hidden;
            background: #f7fafc;
        }

        /* Full Screen Map */
        #map { 
            height: 100vh; 
            width: 100vw; 
            z-index: 1;
            filter: brightness(0.98) saturate(1.1);
        }

        /* Animated Background Pattern */
        #map::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: radial-gradient(circle at 20% 80%, rgba(37, 99, 235, 0.04) 0%, transparent 50%),
                        radial-gradient(circle at 80% 20%, rgba(236, 72, 153, 0.04) 0%, transparent 50%);
            pointer-events: none;
            z-index: 1;
        }

        /* Floating Header Bar */
        #header-bar {
            position: absolute;
            top: 24px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--bg-glass-dark);
            backdrop-filter: blur(20px) saturate(180%);
            padding: 16px 32px;
            border-radius: 100px;
            box-shadow: var(--shadow-md);
            z-index: 1001;
            display: flex;
            align-items: center;
            gap: 16px;
            border: 1px solid rgba(255, 255, 255, 0.6);
            animation: slideDown 0.6s ease-out;
        }

        @keyframes slideDown {
            from { transform: translateX(-50%) translateY(-20px); opacity: 0; }
            to { transform: translateX(-50%) translateY(0); opacity: 1; }
        }

        .header-icon {
            width: 40px;
            height: 40px;
            background: var(--primary-gradient);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            box-shadow: var(--shadow-sm);
        }

        .header-content h1 {
            margin: 0;
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.25rem;
            font-weight: 700;
            background: var(--primary-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .header-content p {
            margin: 2px 0 0 0;
            font-size: 0.8rem;
            color: var(--text-light);
            font-weight: 500;
        }

        /* Enhanced Sidebar */
        #sidebar {
            position: absolute;
            top: 110px;
            left: 24px;
            width: 420px;
            max-height: calc(100vh - 134px);
            background: var(--bg-glass-dark);
            backdrop-filter: blur(20px) saturate(180%);
            border-radius: 24px;
            box-shadow: var(--shadow-lg);
            z-index: 1000;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.6);
            animation: slideInLeft 0.6s ease-out 0.2s both;
        }

        @keyframes slideInLeft {
            from { transform: translateX(-40px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        #sidebar-header {
            padding: 28px;
            background: var(--primary-gradient);
            color: white;
            position: relative;
            overflow: hidden;
        }

        #sidebar-header::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            animation: pulse 4s ease-in-out infinite;
        }

        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 0.5; }
            50% { transform: scale(1.1); opacity: 0.8; }
        }

        #sidebar-header h2 { 
            margin: 0; 
            font-size: 1.4rem; 
            font-weight: 700;
            font-family: 'Space Grotesk', sans-serif;
            letter-spacing: -0.02em;
            position: relative;
            z-index: 1;
        }

        #sidebar-header p { 
            margin: 8px 0 0 0; 
            font-size: 0.9rem; 
            opacity: 0.95;
            font-weight: 400;
            position: relative;
            z-index: 1;
        }

        #sidebar-content {
            padding: 28px;
            overflow-y: auto;
            flex: 1;
        }

        #sidebar-content::-webkit-scrollbar { width: 6px; }
        #sidebar-content::-webkit-scrollbar-track { background: transparent; }
        #sidebar-content::-webkit-scrollbar-thumb { 
            background: linear-gradient(180deg, #2563eb, #7c3aed); 
            border-radius: 10px; 
        }

        /* Loading Overlay */
        #loader {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
            z-index: 9999;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: white;
        }

        .loader-content {
            text-align: center;
            animation: fadeInUp 0.6s ease-out;
        }

        @keyframes fadeInUp {
            from { transform: translateY(20px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }

        .spinner {
            width: 60px; 
            height: 60px;
            border: 4px solid rgba(255, 255, 255, 0.2);
            border-top: 4px solid white;
            border-radius: 50%;
            animation: spin 1s cubic-bezier(0.68, -0.55, 0.265, 1.55) infinite;
            margin-bottom: 24px;
        }

        @keyframes spin { 
            0% { transform: rotate(0deg); } 
            100% { transform: rotate(360deg); } 
        }

        #loader-text {
            font-size: 1.3rem;
            font-weight: 600;
            font-family: 'Space Grotesk', sans-serif;
            margin-bottom: 8px;
        }

        .loader-subtitle {
            font-size: 0.95rem;
            opacity: 0.9;
        }

        /* Metrics Grid */
        .metric-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 14px;
            margin-bottom: 24px;
        }

        .metric-card {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(255, 255, 255, 0.6) 100%);
            padding: 18px;
            border-radius: 16px;
            border: 1px solid rgba(37, 99, 235, 0.1);
            box-shadow: var(--shadow-sm);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }

        .metric-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: var(--primary-gradient);
            transform: scaleX(0);
            transition: transform 0.3s ease;
        }

        .metric-card:hover {
            transform: translateY(-4px);
            box-shadow: var(--shadow-md);
            border-color: rgba(37, 99, 235, 0.3);
        }

        .metric-card:hover::before {
            transform: scaleX(1);
        }

        .metric-label { 
            font-size: 0.75rem; 
            color: var(--text-light); 
            text-transform: uppercase; 
            letter-spacing: 0.08em;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .metric-value { 
            font-size: 1.5rem; 
            font-weight: 700; 
            background: var(--primary-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-family: 'Space Grotesk', sans-serif;
        }

        /* Empty State */
        .empty-state {
            text-align: center;
            padding: 60px 24px;
            color: var(--text-mid);
            background: linear-gradient(135deg, rgba(37, 99, 235, 0.05) 0%, rgba(124, 58, 237, 0.05) 100%);
            border-radius: 20px;
            border: 2px dashed rgba(37, 99, 235, 0.25);
            animation: float 3s ease-in-out infinite;
        }

        @keyframes float {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }

        .empty-icon { 
            font-size: 3.5rem; 
            margin-bottom: 16px; 
            display: block;
            animation: bounce 2s ease-in-out infinite;
        }

        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }

        .empty-state p {
            font-size: 1rem;
            line-height: 1.6;
            margin: 0;
            font-weight: 500;
        }

        /* Chart Container */
        #chart-div { 
            height: 380px; 
            width: 100%;
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.5) 0%, rgba(255, 255, 255, 0.2) 100%);
            border-radius: 16px;
            padding: 16px;
            box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.05);
        }

        /* Stats Summary Badge */
        .stats-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: var(--success-gradient);
            color: white;
            padding: 10px 20px;
            border-radius: 100px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 20px;
            box-shadow: var(--shadow-sm);
            animation: slideIn 0.6s ease-out;
        }

        @keyframes slideIn {
            from { transform: translateX(-20px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        .stats-badge-icon {
            font-size: 1.2rem;
        }

        /* Leaflet Custom Controls */
        .leaflet-control-zoom {
            border: none !important;
            box-shadow: var(--shadow-md) !important;
            border-radius: 12px !important;
            overflow: hidden;
            background: var(--bg-glass-dark) !important;
            backdrop-filter: blur(20px) !important;
        }

        .leaflet-control-zoom a {
            width: 40px !important;
            height: 40px !important;
            line-height: 40px !important;
            font-size: 20px !important;
            font-weight: 700 !important;
            color: #2563eb !important;
            background: transparent !important;
            border: none !important;
            transition: all 0.2s ease !important;
        }

        .leaflet-control-zoom a:hover {
            background: rgba(37, 99, 235, 0.1) !important;
            color: #7c3aed !important;
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            #sidebar {
                width: calc(100% - 48px);
                left: 24px;
                right: 24px;
                max-height: 50vh;
            }

            #header-bar {
                left: 24px;
                right: 24px;
                transform: none;
                border-radius: 20px;
            }

            .metric-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>

    <div id="loader">
        <div class="loader-content">
            <div class="spinner"></div>
            <div id="loader-text">Loading Urban Data</div>
            <div class="loader-subtitle">Preparing street analytics...</div>
        </div>
    </div>

    <div id="header-bar">
        <div class="header-icon">🗺️</div>
        <div class="header-content">
            <h1>Urban Walkability Analytics</h1>
            <p>Interactive Street Segment Analysis Dashboard</p>
        </div>
    </div>

    <div id="sidebar">
        <div id="sidebar-header">
            <h2>Segment Details</h2>
            <p>Click any street to explore metrics</p>
        </div>
        <div id="sidebar-content">
            <div id="details-container" style="display: none;">
                <div class="stats-badge">
                    <span class="stats-badge-icon">📊</span>
                    <span>Selected Segment Analysis</span>
                </div>
                
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-label">Street ID</div>
                        <div class="metric-value" id="val-id">-</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Length</div>
                        <div class="metric-value" id="val-len">-</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Type</div>
                        <div class="metric-value" id="val-type">-</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Overall Score</div>
                        <div class="metric-value" id="val-avg">-</div>
                    </div>
                </div>
                <div id="chart-div"></div>
            </div>

            <div id="empty-state" class="empty-state">
                <span class="empty-icon">🎯</span>
                <p>Select any street segment on the map<br>to view detailed walkability metrics</p>
            </div>
        </div>
    </div>

    <div id="map"></div>

    <script>
        // Init Map
        const map = L.map('map', {
            zoomControl: false
        }).setView({{ center }}, 13);
        
        L.control.zoom({ position: 'bottomright' }).addTo(map);

        // Enhanced base map
        L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; OpenStreetMap &copy; CARTO',
            subdomains: 'abcd',
            maxZoom: 20
        }).addTo(map);

        let highlightLayer = null;

        // Fetch Data
        fetch('/api/data')
            .then(response => response.json())
            .then(data => {
                // Hide loader with fade
                const loader = document.getElementById('loader');
                loader.style.transition = 'opacity 0.5s ease';
                loader.style.opacity = '0';
                setTimeout(() => loader.style.display = 'none', 500);

                const myRenderer = L.canvas({ padding: 0.5 });

                const geoJsonLayer = L.geoJSON(data, {
                    renderer: myRenderer,
                    style: function(feature) {
                        return {
                            color: '#3b82f6',
                            weight: 3,
                            opacity: 0.7,
                            lineCap: 'round',
                            lineJoin: 'round'
                        };
                    },
                    onEachFeature: function(feature, layer) {
                        layer.on('click', function(e) {
                            L.DomEvent.stopPropagation(e);
                            selectSegment(feature.properties, layer);
                        });

                        layer.on('mouseover', function() {
                            if (highlightLayer !== layer) {
                                layer.setStyle({ 
                                    opacity: 1, 
                                    weight: 5, 
                                    color: '#8b5cf6' 
                                });
                            }
                        });

                        layer.on('mouseout', function() {
                            if (highlightLayer !== layer) {
                                geoJsonLayer.resetStyle(layer);
                            }
                        });
                    }
                }).addTo(map);

                if (data.features.length > 0) {
                    map.fitBounds(geoJsonLayer.getBounds());
                }
            })
            .catch(err => {
                document.getElementById('loader-text').innerText = "Error loading data";
                console.error(err);
            });

        map.on('click', function() {
            resetSelection();
        });

        function resetSelection() {
            document.getElementById('details-container').style.display = 'none';
            document.getElementById('empty-state').style.display = 'block';
            if (highlightLayer) {
                highlightLayer.setStyle({
                    color: '#3b82f6',
                    weight: 3,
                    opacity: 0.7
                });
                highlightLayer = null;
            }
        }

        function selectSegment(props, layer) {
            if (highlightLayer) {
                highlightLayer.setStyle({ color: '#3b82f6', weight: 3, opacity: 0.7 });
            }
            highlightLayer = layer;
            layer.setStyle({ 
                color: '#ec4899', 
                weight: 6, 
                opacity: 1.0 
            });
            layer.bringToFront();

            document.getElementById('empty-state').style.display = 'none';
            document.getElementById('details-container').style.display = 'block';

            document.getElementById('val-id').innerText = props.ID_TRC || 'N/A';
            document.getElementById('val-len').innerText = (props.Length || 0).toFixed(1) + 'm';
            document.getElementById('val-type').innerText = props.TYP_VOIE || 'N/A';

            const metrics = {
                'Luminosity': props.LUM_Score || 0,
                'Space for Interaction': props.SFI_score || 0,
                'Greenery': props['G-Score'] || 0,
                'Shade': props.SH_Score || 0,
                'Connectivity': props.CO_Score || 0,
                'Population Density': props.Pop_Score || 0,
                'Slope': props.slope_normalized || 0
            };

            const values = Object.values(metrics);
            const keys = Object.keys(metrics);
            
            const avg = values.reduce((a, b) => a + b, 0) / values.length;
            document.getElementById('val-avg').innerText = avg.toFixed(1);

            renderChart(keys, values);
        }

        function renderChart(labels, values) {
            // Vibrant, distinct colors for each bar
            const colors = [
                '#3b82f6', // Blue
                '#8b5cf6', // Purple
                '#ec4899', // Pink
                '#f97316', // Orange
                '#10b981', // Green
                '#eab308', // Yellow
                '#06b6d4'  // Cyan
            ];

            var data = [{
                type: 'bar',
                x: values,
                y: labels,
                orientation: 'h',
                marker: {
                    color: colors,
                    line: { width: 0 }
                },
                text: values.map(v => v.toFixed(1)),
                textposition: 'outside',
                textfont: { size: 12, weight: 600 },
                hovertemplate: '<b>%{y}</b><br>Score: %{x:.1f}<extra></extra>'
            }];

            var layout = {
                margin: { t: 20, l: 140, r: 40, b: 40 },
                height: 350,
                font: { family: 'Inter', size: 12 },
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                xaxis: { 
                    title: { text: 'Score', font: { size: 13, weight: 600 } },
                    zeroline: false,
                    gridcolor: 'rgba(37, 99, 235, 0.1)',
                    range: [0, Math.max(...values) * 1.2]
                },
                yaxis: { 
                    tickfont: { size: 11, weight: 500 },
                    tickcolor: 'rgba(0,0,0,0)'
                },
                hoverlabel: {
                    bgcolor: 'white',
                    bordercolor: '#2563eb',
                    font: { family: 'Inter', size: 12 }
                }
            };

            var config = { 
                responsive: true, 
                displayModeBar: false 
            };
            
            Plotly.newPlot('chart-div', data, layout, config);
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, center=center_coords)

@app.route('/api/data')
def get_data():
    if geojson_response_cache:
        return jsonify(geojson_response_cache)
    else:
        return jsonify({"error": "Data not loaded"}), 500

def open_browser():
    """Open the browser after a short delay"""
    import time
    time.sleep(1.5)
    webbrowser.open('http://127.0.0.1:5000/')

if __name__ == '__main__':
    load_and_optimize_data()
    
    print("\n Starting optimized server...")
    threading.Timer(1, open_browser).start()
    app.run(debug=False, port=5000)