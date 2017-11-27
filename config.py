#!/usr/bin/env python

import os
import time
import codecs
import argparse
from collections import defaultdict

parser = argparse.ArgumentParser()
parser.add_argument('--train', help='Train set', nargs='+')
parser.add_argument('--dev', help='Dev set', nargs='+')
parser.add_argument('--test', help='Test set', nargs='+')
parser.add_argument('--embeddings', help='Pretrained embeddings', default='./en.polyglot.txt', type=str)
parser.add_argument('--ignore-embeddings', help='Ignore pretrained embeddings', action='store_true')
parser.add_argument('--shared', help='Share embeddings', default=False, type=bool)
parser.add_argument('--multilingual', help='Multilingual embeddings', action='store_true')
parser.add_argument('--freeze', help='Freeze embedding weights', default=False, type=bool)
parser.add_argument('--word-embedding-dim', help='Only if not using pretrained', type=int, default=64)
parser.add_argument('--char-embedding-dim', type=int, default=128)
parser.add_argument('--rnn', help='Use RNN after convolutions', action='store_true')
parser.add_argument('--rnn-dim', help='RNN dim', type=int, default=128)
parser.add_argument('--epochs', help='n epochs', type=int, default=5)
parser.add_argument('--bsize', help='batch size', type=int, default=10)
parser.add_argument('--save', help='Save to hdf5', type=bool, default=False)
parser.add_argument('--hdf5', help='hdf5 fname')
parser.add_argument('--model', help='model type', default='blstm', type=str)
parser.add_argument('--convlen', help='convnet length', default=6, type=int)
parser.add_argument('--chars', help='use characters', action='store_true')
parser.add_argument('--bytes', help='use bytes', action='store_true')
parser.add_argument('--words', help='use words', action='store_true')
parser.add_argument('--nwords', help='use max n words', type=int, default=100000)
parser.add_argument('--bookkeeping', help='bookkeeping directory', type=str)
parser.add_argument('--tag', help='extra experiment nametag', type=str)
parser.add_argument('--tagmap', help='mapping to abstract tags for auxillary loss', type=str, default='./abstract_map.txt')
parser.add_argument('--inception', help='use n inception modules in char embeddings', type=int, default=0)
parser.add_argument('--resnet', help='use resnets', type=int, default=0)
parser.add_argument('--bypass', help='send char info directly to final dense', action='store_true')
parser.add_argument('--mwe', help='handle multi-word expressions', action='store_true', default=True)
parser.add_argument('--shorten-sents', help='attempt to shorten sentences', action='store_true')
parser.add_argument('--max-word-len', help='max length word for char embeds', default=256, type=int)
parser.add_argument('--max-sent-len', help='max length word sequence', default=60, type=int)
parser.add_argument('--early-stopping', help='use early stopping callback', action='store_true')
parser.add_argument('--model-checkpoint', help='save best model', action='store_true')
parser.add_argument('--output', help='system output fname', type=str)
parser.add_argument('--bn', help='use batch normalisation', action='store_true')
parser.add_argument('--dropout', help='use dropout', type=float, default=0.0)
parser.add_argument('--memsave', help='attempt to save memory', action='store_true')
parser.add_argument('--verbose', help='keras verbosity', type=int, default=1)
parser.add_argument('--aux', help='filepath for auxiliary data', nargs='+')

args = parser.parse_args()

# Values for embedding paddings etc.
SENT_START = '<w>'
SENT_END = '</w>'
SENT_PAD = '<PAD>'
SENT_CONT = '##'
UNKNOWN = '_UNK'
NUMBER = '####'

if args.embeddings:
    emb_name = os.path.basename(args.embeddings)
else:
    emb_name = ''

if args.bytes:
    args.chars = True

# Logging name / path
experiment_tag = 'ep-{0}_bsize-{1}_emb-{2}_train-{3}_dev-{4}_test-{10}words-{5}_chars-{6}_inception-{7}_resnet-{8}_time-{9}'.format(
args.epochs,
args.bsize,
emb_name,
os.path.basename(args.train[0]),
os.path.basename(args.dev[0]),
args.words,
args.chars,
args.inception,
args.resnet,
time.time(),
os.path.basename(args.test[0])
)
if args.tag:
    experiment_tag += '_tag-{0}'.format(args.tag)

if args.model_checkpoint and not args.bookkeeping:
    print('bookkeeping directory must be specified if saving models')
    exit()

if args.resnet and args.inception:
    print('cannot use both resnet and inception')
    exit()

if args.bookkeeping:
    experiment_dir = os.path.join(args.bookkeeping, experiment_tag)
    os.mkdir(experiment_dir)
    if not os.path.exists(args.bookkeeping):
        os.mkdir(args.bookkeeping)
elif __debug__:
    print('No bookkeeping directory specified, no run information will be stored.')

if not args.chars and not args.words:
    print("need to specify (either or both): --chars --words")
    exit()
