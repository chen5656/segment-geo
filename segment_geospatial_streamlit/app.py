import requests
import streamlit as st
from streamlit_folium import folium_static
import folium
from folium.plugins import Draw
from streamlit import components

# Page config
st.set_page_config(layout="wide")

# Initialize session state
if 'bbox' not in st.session_state:
    st.session_state.bbox = None

# Title and description
st.title("Geospatial Object Detection")
st.write("Draw a box on the map and enter what you want to detect.")

# Create two columns - left for inputs, right for map
col1, col2 = st.columns([1, 4])  # Changed ratio to make map larger

with col1:
    # Input panel
    st.subheader("Detection Settings")
    
    # Text input for object to detect
    text_prompt = st.text_input(
        "What do you want to detect?",
        placeholder="e.g., poles, trees, buildings"
    )
    
    # Zoom level dropdown
    zoom_level = st.selectbox(
        "Zoom Level",
        options=[15, 16, 17, 18, 19, 20, 21, 22],
        index=3,  # Default to 18
        help="Higher zoom level means more detail"
    )
    
    # Detect button - only enabled if bbox is selected
    detect_button = st.button(
        "Detect Objects",
        # disabled=not st.session_state.bbox,
        help="First draw a rectangle on the map"
    )

with col2:
    # Initialize map centered on a default location
    m = folium.Map(
        location=[32.77058258620389, -96.79199913948932],
        zoom_start=zoom_level,
        width='100%',
        height='800px'  # Increased height for better visibility
    )
    
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
    
    # Display map with full width
    map_data = folium_static(m, width=None, height=800)
    
    # Get bbox from drawn rectangle using JavaScript
    components.v1.html(
        """
        <script>
        // Wait for the map to be loaded
        window.addEventListener('load', function() {
            // Find the map element
            const maps = document.getElementsByClassName('folium-map');
            if (maps.length > 0) {
                const map = maps[0];
                
                // Add draw created event listener
                map.addEventListener('draw:created', function(e) {
                    const layer = e.layer;
                    const bounds = layer.getBounds();
                    const bbox = [
                        bounds.getWest(),
                        bounds.getSouth(),
                        bounds.getEast(),
                        bounds.getNorth()
                    ];
                    // Send bbox to Streamlit
                    window.parent.postMessage({
                        type: 'streamlit:set_session_state',
                        data: { bbox: bbox }
                    }, '*');
                });
            }
        });
        </script>
        """,
        height=0,
    )

# Handle detection
if detect_button and st.session_state.bbox and text_prompt:
    with st.spinner('Detecting objects...'):
        try:
            # Prepare request data
            data = {
                "bbox": st.session_state.bbox,
                "text_prompt": text_prompt,
                "zoom_level": zoom_level  # Added zoom level to the request
            }
            
            # Make API request
            response = requests.post(
                f"{st.secrets.get('API_URL', 'http://api:8000')}/predict",
                json=data
            )
            
            if response.status_code == 200:
                # Get GeoJSON result
                geojson_data = response.json()
                
                # Display results
                st.success(f"Detection complete! Found objects matching '{text_prompt}'")
                
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
3. Select zoom level for detection
4. Click 'Detect Objects' button
5. Download results as GeoJSON if needed
""")


