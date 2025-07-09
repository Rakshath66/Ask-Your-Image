import streamlit as st
from PIL import Image
from transformers import BlipProcessor, BlipForQuestionAnswering, BlipForConditionalGeneration
import torch
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader

# This will scroll smoothly to the very top when the question is selected (after rerun happens).
if "selected_question" in st.session_state and st.session_state.selected_question:
    st.markdown("""
        <script>
            window.onload = function() {
                window.scrollTo({top: 0, behavior: 'smooth'});
            }
        </script>
    """, unsafe_allow_html=True)

@st.cache_resource
def load_models():
    processor = BlipProcessor.from_pretrained("Salesforce/blip-vqa-base")
    vqa_model = BlipForQuestionAnswering.from_pretrained("Salesforce/blip-vqa-base").to("cuda" if torch.cuda.is_available() else "cpu")
    caption_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to(vqa_model.device)
    return processor, vqa_model, caption_model

processor, vqa_model, caption_model = load_models()

st.markdown(
    """
    <h1 style="
        background: linear-gradient(to right, #00FF00, #c2f0ff, #00FF00);
        -webkit-background-clip: text;
        color: transparent;
        font-size: 3rem;
        text-align: center;
        padding: 1rem 0;
    ">
         Ask Your Image
    </h1>
    """,
    unsafe_allow_html=True
)
st.markdown("""<h3 style="text-align: center;">Upload and ask</h3>""", unsafe_allow_html=True)

uploaded_image = st.file_uploader("Upload an image", type=["jpg", "png", "jpeg"])

# question = st.text_input("Ask a question")
with st.form(key="chat_form", clear_on_submit=True):
    question = st.text_input("Ask a question")
    submit = st.form_submit_button("📤 Send", use_container_width=True)
    if submit:
        st.session_state.selected_question = question

with st.expander("⚠️ &nbsp;  Technology Used &nbsp;  ⚠️ ", expanded=False):
    st.markdown("""
    **🤖 Upload an image and ask a question about it.**

    ---
    Technology Used:
    - 📄 BLIP
    - 🌐 ViT
    - 🧮 OpenCV, PIL
    - 📚 Streamlit

    ---
    ### ✅ Example Questions:
    - *"What is the background colour in the image?"*
    - *"Which colour dress does the person in the image wear?"*

    ---
    ### ⚠️ Notes:
    - May make mistakes if facts are unclear – give clear prompt.
    - Avoid vague inputs like “What do you think?” – be specific!
    """)


# ✅ Initialize session state key to avoid attribute error
if "selected_question" not in st.session_state:
    st.session_state.selected_question = ""

if uploaded_image:
    image = Image.open(uploaded_image).convert("RGB")
    # st.image(image, caption="Uploaded Image", use_container_width=True)

    # 📝 Generate Image Caption
    caption_inputs = processor(image, return_tensors="pt").to(caption_model.device)
    caption_ids = caption_model.generate(**caption_inputs)
    caption = processor.decode(caption_ids[0], skip_special_tokens=True)

    question = st.session_state.selected_question
    if question:
        # 🤖 Answer the question
        inputs = processor(image, question, return_tensors="pt").to(vqa_model.device)
        out = vqa_model.generate(**inputs)
        answer = processor.decode(out[0], skip_special_tokens=True)
        # st.markdown("#### 💡 Answer:")
        # st.success(answer)
        st.success(f"#### 💡 Answer: {answer}")
        # st.markdown(f"""
        # <div style='margin-top: 30px; margin-bottom: 15px; padding: 10px; background-color: #111; border-left: 5px solid #00FF00;'>
        #     <h3 style='color: #00FF00; margin: 0;'>💡 Answer: {answer}</h3>
        # </div>
        # """, unsafe_allow_html=True)

        # 3️⃣ 📄 Download PDF Button (Save Q&A as PDF)
        # Convert image for ReportLab
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        img_reader = ImageReader(img_bytes)

        # Create PDF
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, "🧠 Visual Q&A Report")

        c.setFont("Helvetica", 12)
        text_y = height - 100
        c.drawString(50, text_y, f"Question: {question}")
        c.drawString(50, text_y - 30, f"Answer: {answer}")
        c.drawString(50, text_y - 60, f"Caption: {caption}")
        c.drawImage(img_reader, 50, text_y - 400, width=300, height=300) # Draw image (scaled to fit)

        c.save()
        buffer.seek(0)

        st.download_button(
            label="📄 Download Q&A Report with Image",
            data=buffer,
            file_name="qa_report.pdf",
            mime="application/pdf"
        )
    # 4️⃣ Image Preview
    st.image(image, caption=caption, use_container_width=True)

    st.markdown(f"""
        <div style='margin-top: 30px; margin-bottom: 15px; padding: 10px; background-color: #111; border-left: 5px solid #00FF00;'>
            <h3 style='color: #00FF00; margin: 0;'>📝 Auto Caption: </h3>
            <p style='color: #ccc; margin: 5px 0 0;'>{caption}</p>
        </div>
        """, unsafe_allow_html=True)


# 💡 Generate dynamic follow-up questions
if uploaded_image and caption and not question:
    st.markdown("### 💬 Ask a Follow-up Question")
    follow_ups = [
        f"What is happening in the image?",
        f"Where could this scene be located?",
        f"What is the main object in the image?",
        f"What might be the mood of the scene?",
        f"What is the environment like?",
        f"Is this image taken indoors or outdoors?",
    ]
    for q in follow_ups:
        if st.button(q):
            st.session_state.selected_question = q
            # scroll_to_top()  # ✅ Scroll to top before rerun
            st.rerun()
      # st.markdown(f"- {q}")
