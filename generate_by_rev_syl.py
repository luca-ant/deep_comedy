import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import numpy as np
import tensorflow as tf
tf.get_logger().setLevel('ERROR')

from dante_by_rev_syl.data_preparation import text_in_rev_syls, text_in_syls_rhyme
from dante_by_rev_syl.text_processing import clean_comedy, prettify_text, special_tokens
from dante_by_rev_syl.generate_dante import generate_text
from utils import save_vocab, load_vocab

working_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dante_by_rev_syl')

divine_comedy_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "divina_commedia", "divina_commedia_accent_UTF-8.txt") 

with open(divine_comedy_file,"r") as f:
    divine_comedy = f.read()

divine_comedy = clean_comedy(divine_comedy, special_tokens)


#vocab, idx2syl, syl2idx = build_vocab(divine_comedy)


# Path where the vocab is saved
logs_dir = os.path.join(working_dir, 'logs')
os.makedirs(logs_dir, exist_ok = True) 
vocab_file_rhyme = os.path.join(logs_dir, 'vocab_rhyme.json')
vocab_file_verse = os.path.join(logs_dir,  'vocab_verse.json')

vocab_rhyme, idx2syl_rhyme, syl2idx_rhyme = load_vocab(vocab_file_rhyme)
vocab_verse, idx2syl_verse, syl2idx_verse = load_vocab(vocab_file_verse)


# Path where the model is saved
models_dir = os.path.join(working_dir, 'models')
os.makedirs(models_dir, exist_ok = True) 
model_file_verse = os.path.join(models_dir, "dante_by_rev_syl_verse_model.h5")
model_file_rhyme = os.path.join(models_dir, "dante_by_rev_syl_rhyme_model.h5")

model_verse = tf.keras.models.load_model(model_file_verse)
model_rhyme = tf.keras.models.load_model(model_file_rhyme)

# Length of the vocabulary
vocab_size_rhyme = len(vocab_rhyme)
vocab_size_verse = len(vocab_verse)


SEQ_LENGTH_RHYME = model_rhyme.get_layer('embedding').output.shape[1]

EMBEDDING_DIM_RHYME  = model_rhyme.get_layer('embedding').output.shape[2]
for l in model_rhyme.layers:
    if l.name == 'first_lstm':
        RNN_TYPE_RHYME  = '2lstm'
        break
    if l.name == 'last_lstm':
        RNN_TYPE_RHYME  = 'lstm' 
        break
    if l.name == 'first_gru':
        RNN_TYPE_RHYME  = '2gru' 
        break
    if l.name == 'last_gru':
        RNN_TYPE_RHYME  = 'gru' 
        break
if 'lstm' in RNN_TYPE_RHYME :
    RNN_UNITS_RHYME  = model_rhyme.get_layer('last_lstm').output.shape[-1]
if 'gru' in RNN_TYPE_RHYME:
    RNN_UNITS_RHYME  = model_rhyme.get_layer('last_gru').output.shape[-1]


SEQ_LENGTH_VERSE = model_verse.get_layer('embedding').output.shape[1]

EMBEDDING_DIM_VERSE  = model_verse.get_layer('embedding').output.shape[2]
for l in model_verse.layers:
    if l.name == 'first_lstm':
        RNN_TYPE_VERSE  = '2lstm'
        break
    if l.name == 'last_lstm':
        RNN_TYPE_VERSE  = 'lstm' 
        break
    if l.name == 'first_gru':
        RNN_TYPE_VERSE  = '2gru' 
        break
    if l.name == 'last_gru':
        RNN_TYPE_VERSE  = 'gru' 
        break
if 'lstm' in RNN_TYPE_VERSE :
    RNN_UNITS_VERSE  = model_verse.get_layer('last_lstm').output.shape[-1]
if 'gru' in RNN_TYPE_VERSE:
    RNN_UNITS_VERSE  = model_verse.get_layer('last_gru').output.shape[-1]

model_rhyme.summary()
model_verse.summary()

model_filename_rhyme = 'model_by_rev_syl_rhyme_seq{}_emb{}_{}{}'.format(SEQ_LENGTH_RHYME , EMBEDDING_DIM_RHYME , RNN_TYPE_RHYME , RNN_UNITS_RHYME )
model_filename_verse = 'model_by_rev_syl_verse_seq{}_emb{}_{}{}'.format(SEQ_LENGTH_VERSE, EMBEDDING_DIM_VERSE, RNN_TYPE_VERSE, RNN_UNITS_VERSE)


print("\nMODEL RHYME: {}\n".format(model_filename_rhyme))
print("\nMODEL VERSE: {}\n".format(model_filename_verse))

model_filename = 'model_by_rev_syl'

os.makedirs(os.path.join(logs_dir, model_filename), exist_ok = True) 

output_file = os.path.join(logs_dir, model_filename, "output.txt")
raw_output_file = os.path.join(logs_dir, model_filename, "raw_output.txt")



divine_comedy_rhyme = text_in_syls_rhyme(divine_comedy)
#index_eoc = divine_comedy_rhyme.index(special_tokens['END_OF_CANTO']) + 1
indexes = [i for i, x in enumerate(divine_comedy_rhyme) if x == special_tokens['END_OF_CANTO']]
index_eoc = np.random.choice(indexes) + 1
start_seq_rhyme = divine_comedy_rhyme[index_eoc - SEQ_LENGTH_RHYME:index_eoc]


divine_comedy_verse = text_in_rev_syls(divine_comedy)
indexes = [i for i, x in enumerate(divine_comedy_verse) if x == special_tokens['END_OF_VERSO'] and i > SEQ_LENGTH_VERSE]
index_eov = np.random.choice(indexes)
start_seq_verse = divine_comedy_verse[index_eov - SEQ_LENGTH_VERSE:index_eov]



generated_text = generate_text(model_rhyme, model_verse, special_tokens, vocab_size_rhyme, vocab_size_verse, syl2idx_rhyme, idx2syl_rhyme, syl2idx_verse, idx2syl_verse, SEQ_LENGTH_RHYME, SEQ_LENGTH_VERSE, start_seq_rhyme, start_seq_verse, temperature=1.0)

#print(prettify_text(generated_text, special_tokens))

with open(output_file,"w") as f:
    f.write(prettify_text(generated_text, special_tokens))

with open(raw_output_file,"w") as f:
    f.write(generated_text)
