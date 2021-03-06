from collections import OrderedDict
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
import binascii
from flask_admin.contrib.sqla import ModelView
from wtforms import ValidationError
from flask import request
import requests
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash,check_password_hash

import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4

MINING_SENDER = "THE BLOCKCHAIN"
MINING_REWARD = 1
MINING_DIFFICULTY = 2

db = SQLAlchemy()

class Students(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100),unique=True,index=True)
    public_key = db.Column(db.String(), unique=True,index=True)
    private_key = db.Column(db.String())
    pwdhash = db.Column(db.String())

    def __init__(self,email,public_key,private_key,password):
        self.email = email
        self.public_key = public_key
        self.private_key = private_key
        self.password = password
        self.pwdhash = generate_password_hash(password)

    def __repr__(self):
        return '%s' % self.email

    def check_password(self, password):
        return check_password_hash(self.pwdhash, password)


class Institutions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    institution_name = db.Column(db.String())
    email = db.Column(db.String(100),unique=True,index=True)
    public_key = db.Column(db.String(), unique=True,index=True)
    private_key = db.Column(db.String())
    pwdhash = db.Column(db.String())

    def __init__(self,institution_name,email,public_key,private_key,password):
        self.institution_name = institution_name
        self.email = email
        self.public_key = public_key
        self.private_key = private_key
        self.password = password
        self.pwdhash = generate_password_hash(password)

    def __repr__(self):
        return '%s' % self.institution_name

    def check_password(self, password):
        return check_password_hash(self.pwdhash, password)


class Employers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company =  db.Column(db.String())
    email = db.Column(db.String(100),unique=True,index=True)
    public_key = db.Column(db.String(), unique=True,index=True)
    private_key = db.Column(db.String())
    pwdhash = db.Column(db.String())

    def __init__(self,company,email,public_key,private_key,password):
        self.company = company
        self.email = email
        self.public_key = public_key
        self.private_key = private_key
        self.password = password
        self.pwdhash = generate_password_hash(password)

    def __repr__(self):
        return '%s' % self.company

    def check_password(self, password):
        return check_password_hash(self.pwdhash, password)

class Certification:
    def __init__(self, sender_address, sender_private_key, recipient_address, certificate):
        self.sender_address = sender_address
        self.sender_private_key = sender_private_key
        self.recipient_address = recipient_address
        self.certificate = certificate

    def __getattr__(self, attr):
        return self.data[attr]

    def to_dict(self):
        return OrderedDict({'sender_address': self.sender_address,
                            'recipient_address': self.recipient_address,
                            'value': self.certificate})

    def sign_certification(self):
        """
        Sign certification with private key
        """
        private_key = RSA.importKey(binascii.unhexlify(self.sender_private_key))
        signer = PKCS1_v1_5.new(private_key)
        h = SHA.new(str(self.to_dict()).encode('utf8'))
        return binascii.hexlify(signer.sign(h)).decode('ascii')


class Blockchain:

    def __init__(self):
        
        self.certifications = []
        self.chain = []
        self.nodes = set()
        #Generate random number to be used as node_id
        self.node_id = str(uuid4()).replace('-', '')
        #Create genesis block
        self.create_block(0, '00')


    def register_node(self, node_url):
        """
        Add a new node to the list of nodes
        """
        #Checking node_url has valid format
        parsed_url = urlparse(node_url)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'.
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')


    def verify_certification_signature(self, sender_address, signature, certification):
        """
        Check that the provided signature corresponds to transaction
        signed by the public key (sender_address)
        """
        public_key = RSA.importKey(binascii.unhexlify(sender_address))
        verifier = PKCS1_v1_5.new(public_key)
        h = SHA.new(str(certification).encode('utf8'))
        return verifier.verify(h, binascii.unhexlify(signature))


    def submit_certification(self, sender_address, recipient_address, value, signature):
        """
        Add a certificate to certifications array if the signature verified
        """
        certification = OrderedDict({'sender_address': sender_address, 
                                    'recipient_address': recipient_address,
                                    'value': value})

        #Reward for mining a block
        if sender_address == MINING_SENDER:
            self.certifications.append(certification)
            return len(self.chain) + 1
        #Manages certifications from wallet to another wallet
        else:
            certification_verification = self.verify_certification_signature(sender_address, signature, certification)
            if certification_verification:
                self.certifications.append(certification)
                return len(self.chain) + 1
            else:
                return False


    def create_block(self, nonce, previous_hash):
        """
        Add a block of certifications to the blockchain
        """
        block = {'block_number': len(self.chain) + 1,
                'timestamp': time(),
                'certifications': self.certifications,
                'nonce': nonce,
                'previous_hash': previous_hash}

        # Reset the current list of certifications
        self.certifications = []

        self.chain.append(block)
        return block


    def hash(self, block):
        """
        Create a SHA-256 hash of a block
        """
        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        
        return hashlib.sha256(block_string).hexdigest()


    def proof_of_work(self):
        """
        Proof of work algorithm
        """
        last_block = self.chain[-1]
        last_hash = self.hash(last_block)

        nonce = 0
        while self.valid_proof(self.certifications, last_hash, nonce) is False:
            nonce += 1

        return nonce


    def valid_proof(self, certifications, last_hash, nonce, difficulty=MINING_DIFFICULTY):
        """
        Check if a hash value satisfies the mining conditions. This function is used within the proof_of_work function.
        """
        guess = (str(certifications)+str(last_hash)+str(nonce)).encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:difficulty] == '0'*difficulty


    def valid_chain(self, chain):
        """
        check if a bockchain is valid
        """
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            #print(last_block)
            #print(block)
            #print("\n-----------\n")
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Check that the Proof of Work is correct
            #Delete the reward certification
            certifications = block['certifications'][:-1]
            # Need to make sure that the dictionary is ordered. Otherwise we'll get a different hash
            certification_elements = ['sender_address', 'recipient_address', 'value']
            certifications = [OrderedDict((k, certification[k]) for k in certification_elements) for certification in certifications]

            if not self.valid_proof(certifications, block['previous_hash'], block['nonce'], MINING_DIFFICULTY):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        Resolve conflicts between blockchain's nodes
        by replacing our chain with the longest one in the network.
        """
        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            print('http://' + node + '/chain')
            response = requests.get('http://' + node + '/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False


class AdminModelView(ModelView):
    can_delete = True
    page_size = 50
