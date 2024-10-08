# -*- coding: utf-8 -*-
"""Multimodal_RAG.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1Y8Crqu-3H07qgV8XhwsY6dWkV-ZIC8kr
"""

!pip install -q -U transformers==4.37.2
!pip install -q bitsandbytes==0.41.3
!pip install -q git+https://github.com/openai/whisper.git
!pip install -q gradio
!pip install -q gTTS

import torch
from transformers import BitsAndBytesConfig, pipeline

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
)

model_id = "llava-hf/llava-1.5-7b-hf"

pipe = pipeline("image-to-text",
                model = model_id,
                model_kwargs={"quantization_config": quantization_config})

import whisper
import gradio as gr
import time
import warnings
import os
from gtts import gTTS
warnings.filterwarnings("ignore")
from PIL import Image

import nltk
nltk.download('punkt')
from nltk import sent_tokenize

image = Image.open("/content/testimg.png")
image

max_new_tokens = 300

prompt_instruction = """
Describe the image given in as much detail as possible,
Whether it is a painting, a photograph, whatever you undertsand from the picture,
explain that to the user.
"""

prompt = "USER: <image>" + prompt_instruction + "\nASSISTANT:"

output = pipe(image, prompt=prompt, generate_kwargs={"max_new_tokens":200})

print(output[0]["generated_text"])

for sent in sent_tokenize(output[0]["generated_text"]):
  print(sent)

from gtts import gTTS
import numpy as np

torch.cuda.is_available()
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using torch {torch.__version__} ({DEVICE})")

import whisper
model = whisper.load_model("medium", device=DEVICE)

print(
    f"Model is {'Multilingual' if model.is_multilingual else 'English-only'}"
    f" and has {sum(np.prod(p.shape) for p in model.parameters()):,} parameters in total."
)

import re

input = "What is the logo at the upper-right corner of the image?"

image = Image.open("/content/testimg.png")

prompt_instruction = """
Act as an expert in image description, using as much detail as possible, answer the following questions
""" + input

prompt = "USER: <image>" + prompt_instruction + "\nASSISTANT:"

output = pipe(image, prompt=prompt, generate_kwargs={"max_new_tokens":300})


match = re.search(r'ASSISTANT:\s*(.*)', output[0]["generated_text"])

if match:
  extracted_text = match.group(1)
  print(extracted_text)
else:
  print("No match found.")
for sent in sent_tokenize(output[0]["generated_text"]):
  print(sent)

import datetime
import os
tstamp = datetime.datetime.now()
tstamp = str(tstamp).replace(" ", "_")
logfile = f'{tstamp}_log.txt'
def write_history(text):
  with open(logfile, "a", encoding="utf-8") as f:
    f.write(text)
    f.write("\n")
  f.close()

import re
import requests
from PIL import Image

def img_to_txt(input_text, input_image):

  image = Image.open(input_image)

  write_history(f"Input Text: {input_text} - Type: {type(input_text)} - Dir: {dir(input_text)}")
  if type(input_text) == tuple:
    prompt_instruction = """
    Act as an expert in image description, using as much detail as possible, describe the input image given to you.
    """
  else:
    prompt_instruction = """
    Act as an expert in image description, using as much detail as possible, describe the input image given to you.
    """ + input_text

  write_history(f"prompt_instruction: {prompt_instruction}")

  prompt = "USER: <image>" + prompt_instruction + "\nASSISTANT:"

  output = pipe(image, prompt=prompt, generate_kwargs={"max_new_tokens":300})

  if output is not None and len(output[0]["generate_text"]) > 0:
    match = re.search(r'ASSISTANT:\s*(.*)', output[0]["generated_text"])
    if match:
      reply = match.group(1)
    else:
      reply = "No response found."
  else:
    reply = "No response generated."

  return reply

def transcribe(audio):

  if audio is None or audio == " ":
    return (" ", " ", None)

  audio = whisper.load_audio(audio)
  audio = whisper.pad_or_trim(audio)

  mel = whisper.log_mel_spectrogram(audio).to(model.device)

  _, probs = model.detect_language(mel)

  options = whisper.DecodingOptions()
  result = whisper.decode(model, mel, options)
  result_text = result.text

  return result_text

def text_to_speech(text, file_path):
  language = "en",
  audio_obj = gTTS(text=text, lang=language, slow=False)
  audio_obj.save(file_path)
  return file_path

import locale
locale.getpreferredencoding = lambda: "UTF-8"

!ffmpeg -f lavfi -i anullsrc=r=44100:cl=mono -t 10 -q:a 9 -acodec libmp3lame Temp.mp3

import gradio as gr
import base64
import os

def process_inputs(audio_path, image_path):

  speech_to_text = transcribe(audio_path)

  if image_path:
    chatgpt_output = img_to_txt(speech_to_text, image_path)
  else:
    chatgpt_output = "No image provided."

  processed_audio_path = text_to_speech(chatgpt_output, "Temp.mp3")

  return speech_to_text, chatgpt_output, processed_audio_path

# Create the interface
iface = gr.Interface(
    fn=process_inputs,
    inputs=[
        gr.Audio(sources=["microphone"], type="filepath"),
        gr.Image(type="filepath")
    ],
    outputs=[
        gr.Textbox(label="Speech to Text"),
        gr.Textbox(label="ChatGPT Output"),
        gr.Audio("Temp.mp3")
    ],
    title="Learn OpenAI Whisper: Image processing with Whisper and Llava",
    description="Upload an image and interact via voice input and audio response."
)

# Launch the interface
iface.launch(debug=True)
