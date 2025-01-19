import requests
import streamlit as st
from streamlit_folium import folium_static
import folium
from folium.plugins import Draw
from streamlit import components

# Page config
st.set_page_config(layout="wide")

# Title and description
st.title("Geospatial Object Detection")
st.write("Draw a box on the map and enter what you want to detect.")

# Create two columns - left for inputs, right for map
col1, col2 = st.columns([1, 3])

with col1:
    # Input panel
    st.subheader("Detection Settings")
    
    # Text input for object to detect
    text_prompt = st.text_input(
        "What do you want to detect?",
        placeholder="e.g., trees, telephone poles",
        help="Enter a single type of object to detect"
    )
    
    # Zoom level slider
    zoom_level = st.slider(
        "Zoom Level",
        min_value=15,
        max_value=22,
        value=20,
        help="Higher zoom level means more detail"
    )
    
    # Initialize session state for bounding box and button
    if 'bbox' not in st.session_state:
        st.session_state.bbox = None
    
    # Create detect button
    detect_button = st.button(
        "Detect Objects",
        disabled=not (st.session_state.bbox and text_prompt),
        help="Draw a box on the map first"
    )

with col2:
    # Initialize map centered on a default location
    m = folium.Map(location=[32.77058258620389, -96.79199913948932], zoom_start=18)
    
    # Add satellite tile layer
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google Satellite',
        name='Satellite'
    ).add_to(m)
    
    # Add draw control
    draw = Draw(
        draw_options={
            'rectangle': True,
            'polygon': False,
            'polyline': False,
            'circle': False,
            'marker': False,
            'circlemarker': False
        },
        edit_options={'edit': False}
    )
    draw.add_to(m)
    
    # Display map
    map_data = folium_static(m, width=800)
    
    # Get bbox from drawn rectangle using JavaScript
    components.html(
        """
        <script>
        const map = document.querySelector("#map");
        map.addEventListener('draw:created', function(e) {
            const bounds = e.layer.getBounds();
            const bbox = [
                bounds.getWest(),
                bounds.getSouth(),
                bounds.getEast(),
                bounds.getNorth()
            ];
            window.parent.postMessage({type: 'bbox', value: bbox}, '*');
        });
        </script>
        """,
        height=0,
    )

# Handle bbox updates from JavaScript
if st.session_state.bbox:
    st.write("Selected area:", st.session_state.bbox)

# Handle detection
if detect_button:
    with st.spinner('Detecting objects...'):
        try:
            # Prepare request data
            data = {
                "bounding_box": st.session_state.bbox,
                "text_prompt": text_prompt,
                "zoom_level": zoom_level
            }
            
            # Make API request
            response = requests.post(
                "http://localhost:8000/predict",
                json=data
            )
            
            if response.status_code == 200:
                geojson_data = response.json()["geojson"]
                
                # Add GeoJSON to map
                folium.GeoJson(
                    geojson_data,
                    name='Detected Objects',
                    style_function=lambda x: {
                        'fillColor': '#00ff00',
                        'color': '#00ff00',
                        'weight': 2,
                        'fillOpacity': 0.3
                    }
                ).add_to(m)
                
                # Add layer control
                folium.LayerControl().add_to(m)
                
                # Update map
                folium_static(m, width=800)
                
                # Add download button for GeoJSON
                st.download_button(
                    label="Download GeoJSON",
                    data=str(geojson_data),
                    file_name="detection_results.geojson",
                    mime="application/json"
                )
                
            else:
                st.error("Error making prediction. Please try again.")
                
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Add instructions at the bottom
st.markdown("""
### How to use:
1. Draw a rectangle on the map to select an area
2. Enter what you want to detect in the text input
3. Adjust zoom level if needed
4. Click 'Detect Objects' button
5. Download results as GeoJSON if needed
""")


