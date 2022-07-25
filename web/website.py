#!/usr/bin/env python3
import streamlit as st

# Initialization #
try:
    NO_INIT = not st.session_state['init']
except:
    NO_INIT = True

if NO_INIT:
    st.session_state['init'] = True

    ## Imports ##
    import re
    import pickle
    import tensorflow as tf
    from keras.utils.data_utils import pad_sequences
    import numpy as np
    import torch
    from transformers import AutoTokenizer
    from transformers import AutoModelForSequenceClassification
    ## End of Imports ##

    ## Parameters ##
    full_size_bilstm_model_path = 'models/bilstm.h5'
    full_size_bilstm_tokenizer_path = 'models/tokenizerBilstm.pickle'
    full_size_bilstm_lower_model_path = 'models/bilstmLower.h5'
    full_size_bilstm_lower_tokenizer_path = 'models/tokenizerBilstmLower.pickle'

    size_2_bilstm_model_path = 'models/bilstmSize2.h5'
    size_2_bilstm_tokenizer_path = 'models/tokenizerBilstmSize2.pickle'
    size_2_bilstm_lower_model_path = 'models/bilstmSize2Lower.h5'
    size_2_bilstm_lower_tokenizer_path = 'models/tokenizerBilstmSize2Lower.pickle'

    size_3_bilstm_model_path = 'models/bilstmSize3.h5'
    size_3_bilstm_tokenizer_path = 'models/tokenizerBilstmSize3.pickle'
    size_3_bilstm_lower_model_path = 'models/bilstmSize3Lower.h5'
    size_3_bilstm_lower_tokenizer_path = 'models/tokenizerBilstmSize3Lower.pickle'

    full_size_mbert_model_path = 'models/mbert'
    full_size_mbert_lower_model_path = 'models/mbertLower'

    mbert_tokenizer_path = 'models/tokenizerMbert'
    ## End of parameters ##

    ## Load models ##
    with tf.device('/cpu:0'):
        full_size_bilstm_model = tf.keras.models.load_model(full_size_bilstm_model_path)
        full_size_bilstm_lower_model = tf.keras.models.load_model(full_size_bilstm_lower_model_path)

        size_2_bilstm_model = tf.keras.models.load_model(size_2_bilstm_model_path)
        size_2_bilstm_lower_model = tf.keras.models.load_model(size_2_bilstm_lower_model_path)

        size_3_bilstm_model = tf.keras.models.load_model(size_3_bilstm_model_path)
        size_3_bilstm_lower_model = tf.keras.models.load_model(size_3_bilstm_lower_model_path)
    
    with open(full_size_bilstm_tokenizer_path, 'rb') as handle:
        full_size_bilstm_tokenizer = pickle.load(handle)
    with open(full_size_bilstm_lower_tokenizer_path, 'rb') as handle:
        full_size_bilstm_lower_tokenizer = pickle.load(handle)
    
    with open(size_2_bilstm_tokenizer_path, 'rb') as handle:
        size_2_bilstm_tokenizer = pickle.load(handle)
    with open(size_2_bilstm_lower_tokenizer_path, 'rb') as handle:
        size_2_bilstm_lower_tokenizer = pickle.load(handle)
    
    with open(size_3_bilstm_tokenizer_path, 'rb') as handle:
        size_3_bilstm_tokenizer = pickle.load(handle)
    with open(size_3_bilstm_lower_tokenizer_path, 'rb') as handle:
        size_3_bilstm_lower_tokenizer = pickle.load(handle)
    
    full_size_mbert_model = AutoModelForSequenceClassification.from_pretrained(full_size_mbert_model_path, num_labels=3)
    for param in full_size_mbert_model.parameters():
        param.requires_grad_(False)
    full_size_mbert_lower_model = AutoModelForSequenceClassification.from_pretrained(full_size_mbert_lower_model_path, num_labels=3)
    for param in full_size_mbert_lower_model.parameters():
        param.requires_grad_(False)

    mbert_tokenizer = AutoTokenizer.from_pretrained(mbert_tokenizer_path)
    ## End of load models ##

    ## Functions ##
    ### Clean the text
    def cleanText(text):
        text = text.replace("“", '"').replace(
            "”", '"').replace("‘", "'").replace("’", "'")
        # replace non ascii char but keep the maori chars
        text = re.sub(r'[^\x00-\x7FāēīōūĀĒĪŌŪ]+', '', text)
        text = text.replace('\r', '  ').replace(
            '\n', '  ').replace('\t', '  ')  # remove \r \n \t
        text = text.replace(':', ': ').replace(';', '; ').replace(
            ',', ', ').replace('.', '. ')  # add space after the symbols
        while '  ' in text:
            text = text.replace('  ',  ' ')  # remove redundant spaces
        text = text.replace(' :', ':').replace(' ;', ';').replace(
            ' ,', ',').replace(' .', '.')  # remove space before the symbols
        # handle a.m and p.m
        text = text.replace('a. m', 'a.m').replace('p. m', 'p.m')
        return text.strip()

    ### BiLSTM model ###
    #### Detect the code switching point in a dynamic window
    def sentenceCategory(sentence, padding_length, tokenizer, loaded_model):
        seq = tokenizer.texts_to_sequences([sentence])
        padded = pad_sequences(seq, maxlen=padding_length)
        predict = loaded_model.predict(padded) 
        classw = np.argmax(predict,axis=1)
        return int(classw[0])

    def detectCodeSwitchingPointDynamicWindowVersion(x, w, tokenizer, loaded_model):
        p = w
        words_list = x.split()
        end = len(words_list)
        if w >= end and end > 2:
            w = end - 1
        elif end == 1:
            w = 1
        elif end == 2:
            w = 2
        else:
            pass

        if end < 1:
            return []

        elif end < 2:
            if re.search(u'[āēīōūĀĒĪŌŪ]', x):
                return [1]
            elif re.search(u'[bBcCdDfFgGjJlLqQsSvVxXyYzZ]', x):
                return [2]
            else:
                return [sentenceCategory(x, p, tokenizer, loaded_model)]

        elif end == 2:
            if not re.search(u'[āēīōūĀĒĪŌŪ]', x):
                tmp_result = sentenceCategory(x, p, tokenizer, loaded_model)
                if tmp_result == 1 and not re.search(u'[bBcCdDfFgGjJlLqQsSvVxXyYzZ]', x):
                    return [1, 1]
                elif tmp_result == 2:
                    return [2, 2]
                else:
                    if sentenceCategory(words_list[0], p, tokenizer, loaded_model) == 1 and not re.search(u'[bBcCdDfFgGjJlLqQsSvVxXyYzZ]', words_list[0]):
                        return [1, 2]
                    else:
                        return [2, 1]
            else:
                tmp_char_0 = re.search(u'[āēīōūĀĒĪŌŪ]', words_list[0])
                tmp_char_1 = re.search(u'[āēīōūĀĒĪŌŪ]', words_list[1])
                if tmp_char_0 and tmp_char_1:
                    return [1, 1]
                if tmp_char_0 and not tmp_char_1:
                    return [1, 2]
                else:
                    return [2, 1]
        
        else:
            result = []
            ptr = 0
            while ptr < end:
                this_window = words_list[ptr:ptr+w]
                if ptr + w > end:
                    w = end - ptr
                else:
                    pass

                tmp_result = sentenceCategory(" ".join(this_window), p, tokenizer, loaded_model)
                if tmp_result == 1 and not re.search(u'[bBcCdDfFgGjJlLqQsSvVxXyYzZ]', " ".join(this_window)):
                    result.extend([1 for _ in range(w)])
                elif tmp_result == 2 and not re.search(u'[āēīōūĀĒĪŌŪ]', " ".join(this_window)):
                    result += [2 for _ in range(w)]
                else:
                    if w >= 4 and w % 2 == 0:
                        result += detectCodeSwitchingPointDynamicWindowVersion(" ".join(this_window), w-2, tokenizer, loaded_model)
                    else:
                        result += detectCodeSwitchingPointDynamicWindowVersion(" ".join(this_window), w-1, tokenizer, loaded_model)
                ptr += w
            return result
    ### End of BiLSTM model ###

    ### MBERT model ###
    @torch.no_grad()
    def sentenceCategoryMbertVersion(text: str, model) -> int:
        tokenized_text = mbert_tokenizer(text, padding="longest", truncation=True, return_tensors='pt')
        prediction = model(input_ids=tokenized_text["input_ids"], attention_mask=tokenized_text["attention_mask"], token_type_ids=tokenized_text["token_type_ids"])
        return prediction.logits.detach().cpu().numpy().argmax()

    def detectCodeSwitchingPointMbertVersion(x: str, w: int, model) -> list():
        words_list = x.split()
        end = len(words_list)
        if w >= end and end > 2:
            w = end - 1
        elif end == 1:
            w = 1
        elif end == 2:
            w = 2
        else:
            pass

        if end < 1:
            return []

        elif end == 1:
            if re.search(u'[āēīōūĀĒĪŌŪ]', x):
                return [1]
            elif re.search(u'[bBcCdDfFgGjJlLqQsSvVxXyYzZ]', x):
                return [2]
            else:
                return [sentenceCategoryMbertVersion(x, model)]

        elif end == 2:
            if not re.search(u'[āēīōūĀĒĪŌŪ]', x):
                tmp_result = sentenceCategoryMbertVersion(x, model)
                if tmp_result == 1 and not re.search(u'[bBcCdDfFgGjJlLqQsSvVxXyYzZ]', x):
                    return [1, 1]
                elif tmp_result == 2:
                    return [2, 2]
                else:
                    if sentenceCategoryMbertVersion(words_list[0], model) == 1 and not re.search(u'[bBcCdDfFgGjJlLqQsSvVxXyYzZ]', words_list[0]):
                        return [1, 2]
                    else:
                        return [2, 1]
            else:
                if re.search(u'[āēīōūĀĒĪŌŪ]', words_list[0]) and re.search(u'[āēīōūĀĒĪŌŪ]', words_list[1]):
                    return [1, 1]
                if re.search(u'[āēīōūĀĒĪŌŪ]', words_list[0]) and not re.search(u'[āēīōūĀĒĪŌŪ]', words_list[1]):
                    return [1, 2]
                else:
                    return [2, 1]
        
        else:
            result = []
            ptr = 0
            while ptr < end:
                this_window = words_list[ptr:ptr+w]
                if ptr + w > end:
                    w = end - ptr
                else:
                    pass
                if sentenceCategoryMbertVersion(" ".join(this_window), model) == 1 and not re.search(u'[bBcCdDfFgGjJlLqQsSvVxXyYzZ]', " ".join(this_window)):
                    result.extend([1 for _ in range(w)])
                elif sentenceCategoryMbertVersion(" ".join(this_window), model) == 2 and not re.search(u'[āēīōūĀĒĪŌŪ]', " ".join(this_window)):
                    result += [2 for _ in range(w)]
                else:
                    if w >= 4 and w % 2 == 0:
                        result += detectCodeSwitchingPointMbertVersion(" ".join(this_window), w-2, model)
                    else:
                        result += detectCodeSwitchingPointMbertVersion(" ".join(this_window), w-1, model)
                ptr += w
            return result
    ### End of Mbert model ###
    ## End of functions ##

    ## ST states ##
    st.session_state['full_size_bilstm_model'] = full_size_bilstm_model
    st.session_state['full_size_bilstm_tokenizer'] = full_size_bilstm_tokenizer
    st.session_state['full_size_bilstm_lower_model'] = full_size_bilstm_lower_model
    st.session_state['full_size_bilstm_lower_tokenizer'] = full_size_bilstm_lower_tokenizer

    st.session_state['size_2_bilstm_model'] = size_2_bilstm_model
    st.session_state['size_2_bilstm_tokenizer'] = size_2_bilstm_tokenizer
    st.session_state['size_2_bilstm_lower_model'] = size_2_bilstm_lower_model
    st.session_state['size_2_bilstm_lower_tokenizer'] = size_2_bilstm_lower_tokenizer

    st.session_state['size_3_bilstm_model'] = size_3_bilstm_model
    st.session_state['size_3_bilstm_tokenizer'] = size_3_bilstm_tokenizer
    st.session_state['size_3_bilstm_lower_model'] = size_3_bilstm_lower_model
    st.session_state['size_3_bilstm_lower_tokenizer'] = size_3_bilstm_lower_tokenizer

    st.session_state['full_size_mbert_model'] = full_size_mbert_model
    st.session_state['full_size_mbert_lower_model'] = full_size_mbert_lower_model

    st.session_state['cleanText'] = cleanText
    st.session_state['detectCodeSwitchingPointDynamicWindowVersion'] = detectCodeSwitchingPointDynamicWindowVersion
    st.session_state['detectCodeSwitchingPointMbertVersion'] = detectCodeSwitchingPointMbertVersion
    ## End of ST states ##

    st.session_state['dropdown_models'] = ['Size 2 BiLSTM', 'Size 2 BiLSTM Lower', 'Size 3 BiLSTM', 'Size 3 BiLSTM Lower', 'Full Size BiLSTM', 'Full Size BiLSTM Lower', 'Full Size MBERT', 'Full Size MBERT Lower']
    st.session_state['selected_model'] = 'Size 3 BiLSTM Lower'
    st.session_state['user_input'] = ''
    st.session_state['result'] = ''

# End of initialization #

# The page #
st.set_page_config(
    layout='wide',
    page_title="M/E CW Detection",
    page_icon="https://aotearoavoices.nz/favicon.ico",
    menu_items={
        'Get Help': 'https://speechresearch.auckland.ac.nz/',
        'Report a bug': "https://speechresearch.auckland.ac.nz/",
        'About': "### Speech Research Group @ UoA"
    }
)

## Hide the menu and footer
hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
"""
st.markdown(hide_menu_style, unsafe_allow_html=True)

UoA_logo = '''https://blogs.auckland.ac.nz/files/2016/07/UOA-NT-HC-RGB-1dr6b6b.png'''
Speech_Group_logo = '''https://avatars.githubusercontent.com/u/100390597'''
st.markdown(f'<div style="display:flex;justify-content:flex-start;align-items:center;gap:15px;"><a href="https://www.auckland.ac.nz/"><img src="{UoA_logo}" height="91" /></a><a href="https://speechresearch.auckland.ac.nz/"><img src="{Speech_Group_logo}" style="height:151px;" /></a></div>', unsafe_allow_html=True)

title = st.title('English Māori Code-switching Point Detection Tool')

user_input = st.session_state['cleanText'](st.text_area("This tool detects the code-switching point of English and Māori.", value=st.session_state['user_input'], placeholder="Start typing here...", height=200, max_chars=2500, help="English and Māori only.\n\nThe maximum number of characters is 2500.\n\nNon Ascii and non Māori characters will be ignored."))

with st.container():
    col1, col2 = st.columns([1,1])
    selected_model = col1.selectbox("Select a model:", st.session_state['dropdown_models'], index=3)
    
    col2.markdown("###### ​", unsafe_allow_html=True)

    st.session_state['user_input'] = user_input if user_input else ' '
    detection_button = True if col2.button("Detect", disabled=user_input == '') else False
    user_input = user_input if user_input else ' '
    
    if detection_button:
        st.session_state['selected_model'] = selected_model

        if selected_model == 'Size 2 BiLSTM':
            result = st.session_state['detectCodeSwitchingPointDynamicWindowVersion'](user_input, 2, st.session_state['size_2_bilstm_tokenizer'], st.session_state['size_2_bilstm_model'])
        elif selected_model == 'Size 2 BiLSTM Lower':
            result = st.session_state['detectCodeSwitchingPointDynamicWindowVersion'](user_input.lower(), 2, st.session_state['size_2_bilstm_lower_tokenizer'], st.session_state['size_2_bilstm_lower_model'])
        
        elif selected_model == 'Size 3 BiLSTM':
            result = st.session_state['detectCodeSwitchingPointDynamicWindowVersion'](user_input, 3, st.session_state['size_3_bilstm_tokenizer'], st.session_state['size_3_bilstm_model'])
        elif selected_model == 'Size 3 BiLSTM Lower':
            result = st.session_state['detectCodeSwitchingPointDynamicWindowVersion'](user_input.lower(), 3, st.session_state['size_3_bilstm_lower_tokenizer'], st.session_state['size_3_bilstm_lower_model'])

        elif selected_model == 'Full Size BiLSTM':
            result = st.session_state['detectCodeSwitchingPointDynamicWindowVersion'](user_input, 250, st.session_state['full_size_bilstm_tokenizer'], st.session_state['full_size_bilstm_model'])
        elif selected_model == 'Full Size BiLSTM Lower':
            result = st.session_state['detectCodeSwitchingPointDynamicWindowVersion'](user_input.lower(), 250, st.session_state['full_size_bilstm_lower_tokenizer'], st.session_state['full_size_bilstm_lower_model'])
        
        elif selected_model == 'Full Size MBERT':
            result = st.session_state['detectCodeSwitchingPointMbertVersion'](user_input, 4, st.session_state['full_size_mbert_model'])
        elif selected_model == 'Full Size MBERT Lower':
            result = st.session_state['detectCodeSwitchingPointMbertVersion'](user_input.lower(), 4, st.session_state['full_size_mbert_lower_model'])
        
        else:
            st.error("Please select a model.") ## NEVER HAPPENS
        
        ## 1 for Māori, 2 for English
        result = result if result else [' ']
        tmp_user_input_list = st.session_state['cleanText'](user_input).split()
        tmp_user_input_list = tmp_user_input_list if tmp_user_input_list else [' ']
        tmp_result_str = ""
        tmp_result_till_last_one = result[:-1]
        tmp_result_last_one = result[-1]
        tmp_user_input_last_one = tmp_user_input_list[-1]
        for index, item in enumerate(tmp_result_till_last_one):
            if item == 1:
                tmp_result_str += f'<label style="padding-right:5px;background-color:yellow;font-weight:550">{tmp_user_input_list[index]}</label>'
            elif item == 2:
                tmp_result_str += f'<label style="padding-right:5px;">{tmp_user_input_list[index]}</label>'
            else:
                pass
        
        if tmp_result_last_one == 1:
            tmp_result_str += f'<label style="background-color:yellow;font-weight:550">{tmp_user_input_last_one}</label>'
        elif tmp_result_last_one == 2:
            tmp_result_str += f'<label>{tmp_user_input_last_one}</label>'
        else:
            pass
        
        st.session_state['result'] = tmp_result_str
    
st.markdown("---")
st.markdown(f'#### Result:\n\n<div style="background-color:#f0f2f6;width:100%;height:120px;border-radius:3px;padding:16px;">{st.session_state["result"]}</div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown("For more information of the definition of code switch detection and the models used, please visit: https://openreview.net/forum?id=rAxl_GibSWq")

st.markdown('<div style="position:fixed;bottom:0;background-color:white;width:93%"><div style="text-align:center"><label style="padding-right:4px;">Copyright © 2022</label><a href="https://speechresearch.auckland.ac.nz/">Speech Research Group @ UoA</a><label>. All rights reserved.</label></div></div>', unsafe_allow_html=True)
# End of the page #