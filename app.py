#!/usr/bin/env python3
"""
LegalZen - Premium Legal Document Simplifier Backend
Flask application with AI-powered document analysis and clause explanation.
"""

from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import os
import json
import logging
from datetime import datetime
import traceback
import re
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}

class DocumentProcessor:
    """Handles document parsing and text extraction"""
    
    @staticmethod
    def allowed_file(filename: str) -> bool:
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    @staticmethod
    def extract_text_from_txt(file_path: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as file:
                    return file.read()
            except Exception as e:
                logger.error(f"Error reading text file: {e}")
                return "Error reading file content"
    
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        """Basic PDF text extraction (requires PyPDF2)"""
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except ImportError:
            return "PDF processing requires PyPDF2. Please upload a TXT file instead or install PyPDF2."
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            return "Error processing PDF file"
    
    @staticmethod
    def extract_text_from_docx(file_path: str) -> str:
        """Basic DOCX text extraction (requires python-docx)"""
        try:
            from docx import Document
            doc = Document(file_path)
            text = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text.append(paragraph.text)
            return "\n".join(text)
        except ImportError:
            return "DOCX processing requires python-docx. Please upload a TXT file instead or install python-docx."
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {e}")
            return "Error processing DOCX file"
    
    @classmethod
    def extract_text(cls, file_path: str) -> str:
        """Extract text based on file extension"""
        file_ext = file_path.rsplit('.', 1)[1].lower()
        
        if file_ext == 'pdf':
            return cls.extract_text_from_pdf(file_path)
        elif file_ext == 'docx':
            return cls.extract_text_from_docx(file_path)
        elif file_ext in ['txt', 'doc']:
            return cls.extract_text_from_txt(file_path)
        else:
            return f"Unsupported file type: {file_ext}"

class LegalAnalyzer:
    """Rule-based legal document analysis"""
    
    def __init__(self):
        self.legal_keywords = {
            'contract_terms': ['agreement', 'contract', 'terms', 'conditions', 'party', 'parties'],
            'compensation': ['salary', 'wage', 'compensation', 'payment', 'remuneration', 'benefits'],
            'termination': ['termination', 'terminate', 'end', 'conclusion', 'expiry', 'notice'],
            'confidentiality': ['confidential', 'non-disclosure', 'nda', 'proprietary', 'trade secret'],
            'liability': ['liability', 'responsible', 'damages', 'indemnify', 'negligence'],
            'intellectual_property': ['copyright', 'trademark', 'patent', 'intellectual property', 'ip'],
            'non_compete': ['non-compete', 'competition', 'competitor', 'restraint of trade']
        }
    
    def simple_sentence_tokenize(self, text: str) -> List[str]:
        """Basic sentence tokenization without NLTK"""
        sentences = []
        current_sentence = ""
        
        for char in text:
            current_sentence += char
            if char in ['.', '!', '?', ';']:
                sentence = current_sentence.strip()
                if len(sentence) > 10:  # Filter out very short sentences
                    sentences.append(sentence)
                current_sentence = ""
        
        # Add remaining text if any
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        return sentences
    
    def analyze_document(self, text: str) -> Dict:
        """Main document analysis function"""
        try:
            # Extract clauses
            clauses = self.extract_clauses(text)
            
            # Generate summary
            summary = self.generate_summary(text, clauses)
            
            # Simplify clauses
            simplified_clauses = []
            for clause in clauses:
                simplified = self.simplify_clause(clause)
                simplified_clauses.append(simplified)
            
            return {
                'summary': summary,
                'clauses': simplified_clauses,
                'document_type': self.identify_document_type(text),
                'key_points': self.extract_key_points(text)
            }
        
        except Exception as e:
            logger.error(f"Error in document analysis: {e}")
            return self.get_fallback_analysis(text)
    
    def extract_clauses(self, text: str) -> List[str]:
        """Extract important clauses from legal text"""
        sentences = self.simple_sentence_tokenize(text)
        
        # Identify clause boundaries
        clauses = []
        current_clause = []
        
        for sentence in sentences:
            # Check if sentence starts a new clause
            if self.is_clause_start(sentence) and current_clause:
                clause_text = ' '.join(current_clause)
                if len(clause_text.split()) > 15:  # Only include substantial clauses
                    clauses.append(clause_text)
                current_clause = [sentence]
            else:
                current_clause.append(sentence)
        
        # Add final clause
        if current_clause:
            clause_text = ' '.join(current_clause)
            if len(clause_text.split()) > 15:
                clauses.append(clause_text)
        
        # Filter clauses with legal content
        filtered_clauses = []
        for clause in clauses:
            if self.contains_legal_content(clause):
                filtered_clauses.append(clause.strip())
        
        return filtered_clauses[:8]  # Limit to top 8 clauses
    
    def is_clause_start(self, sentence: str) -> bool:
        """Check if sentence likely starts a new clause (enhanced)"""
        clause_indicators = [
            r'^\d+\.', r'^\([a-z]\)', r'^[A-Z][A-Z\s]+:',
            r'^WHEREAS', r'^NOW THEREFORE', r'^Section \d+',
            r'^Article \d+', r'^Clause \d+', r'^\d+\.\d+',
            r'^THE PARTIES AGREE', r'^IT IS AGREED', r'^IN WITNESS WHEREOF'
        ]
        
        sentence_clean = sentence.strip()
        for pattern in clause_indicators:
            if re.match(pattern, sentence_clean):
                return True
        
        # Check for paragraph headings that are capitalized
        if len(sentence_clean.split()) < 8 and sentence_clean.isupper():
            return True
            
        return False
    
    def contains_legal_content(self, text: str) -> bool:
        """Check if text contains legal keywords"""
        text_lower = text.lower()
        legal_word_count = 0
        
        for category, keywords in self.legal_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    legal_word_count += 1
        
        # Require at least 2 legal keywords for a clause
        return legal_word_count >= 2
    
    def simplify_clause(self, clause: str) -> Dict:
        """Simplify a legal clause using rule-based methods"""
        simplified = clause
        
        # Replace complex legal terms with simpler alternatives
        replacements = {
            'whereas': 'since',
            'heretofore': 'before now',
            'hereinafter': 'from now on',
            'pursuant to': 'according to',
            'notwithstanding': 'despite',
            'in consideration of': 'in exchange for',
            'shall': 'must',
            'shall not': 'must not',
            'may not': 'cannot',
            'such': 'this',
            'said': 'the mentioned',
            'aforementioned': 'mentioned above',
            'hereunder': 'under this agreement',
            'thereof': 'of this',
            'whereby': 'by which',
            'herein': 'in this document'
        }
        
        # Apply replacements
        for legal_term, simple_term in replacements.items():
            pattern = r'\b' + re.escape(legal_term) + r'\b'
            simplified = re.sub(pattern, simple_term, simplified, flags=re.IGNORECASE)
        
        # Remove excessive legal formatting
        simplified = re.sub(r'\s+', ' ', simplified)  # Remove extra whitespace
        simplified = simplified.strip()
        
        # Generate explanation
        explanation = self.generate_explanation(clause)
        title = self.generate_clause_title(clause)
        
        return {
            'title': title,
            'original': clause,
            'simplified': simplified,
            'explanation': explanation
        }
    
    def generate_clause_title(self, clause: str) -> str:
        """Generate a descriptive title for a clause"""
        text_lower = clause.lower()
        
        # Check for specific clause types based on keywords
        if any(word in text_lower for word in ['salary', 'wage', 'compensation', 'payment', 'remuneration']):
            return "💰 Compensation & Payment"
        elif any(word in text_lower for word in ['termination', 'terminate', 'end', 'notice']):
            return "📋 Termination Conditions"
        elif any(word in text_lower for word in ['confidential', 'non-disclosure', 'proprietary', 'secret']):
            return "🔒 Confidentiality Agreement"
        elif any(word in text_lower for word in ['liability', 'damages', 'responsible', 'indemnify']):
            return "⚖️ Liability & Damages"
        elif any(word in text_lower for word in ['intellectual property', 'copyright', 'patent', 'trademark']):
            return "💡 Intellectual Property"
        elif any(word in text_lower for word in ['non-compete', 'competition', 'competitor']):
            return "🚫 Non-Compete Clause"
        elif any(word in text_lower for word in ['duties', 'responsibilities', 'obligations', 'perform']):
            return "📝 Duties & Responsibilities"
        elif any(word in text_lower for word in ['benefits', 'insurance', 'vacation', 'leave']):
            return "🎯 Benefits & Perks"
        else:
            return "📄 General Terms"
    
    def generate_explanation(self, clause: str) -> str:
        """Generate explanation based on clause content"""
        text_lower = clause.lower()
        
        if any(word in text_lower for word in ['salary', 'wage', 'compensation']):
            return "This clause defines how much you'll be paid, when you'll receive payments, and any deductions that may apply."
        elif 'termination' in text_lower:
            return "This section explains the conditions under which employment can be ended, including notice requirements and procedures."
        elif any(word in text_lower for word in ['confidential', 'non-disclosure']):
            return "This requires you to keep company information private and not share sensitive data with unauthorized parties."
        elif 'liability' in text_lower:
            return "This clause defines who is responsible for damages, losses, or legal issues that might arise."
        elif any(word in text_lower for word in ['intellectual property', 'copyright']):
            return "This covers ownership of ideas, inventions, or creative work produced during employment."
        elif 'non-compete' in text_lower:
            return "This restricts your ability to work for competitors or start competing businesses for a specified period."
        elif any(word in text_lower for word in ['duties', 'responsibilities']):
            return "This outlines what tasks and responsibilities you're expected to fulfill in your role."
        elif 'benefits' in text_lower:
            return "This describes additional compensation like health insurance, vacation time, or other employee perks."
        else:
            return "This is a standard legal provision that defines rights, obligations, or procedures for the parties involved."
    
    def generate_summary(self, text: str, clauses: List[str]) -> str:
        """Generate document summary using rule-based approach"""
        doc_type = self.identify_document_type(text)
        word_count = len(text.split())
        clause_count = len(clauses)
        
        # Build summary based on document content
        summary_parts = []
        
        # Document basics
        summary_parts.append(f"This {doc_type} contains {clause_count} main sections with approximately {word_count} words.")
        
        # Identify key themes
        text_lower = text.lower()
        themes = []
        
        if any(word in text_lower for word in ['employment', 'employee', 'employer']):
            themes.append("employment terms")
        if any(word in text_lower for word in ['salary', 'compensation', 'payment']):
            themes.append("compensation details")
        if any(word in text_lower for word in ['termination', 'notice']):
            themes.append("termination procedures")
        if any(word in text_lower for word in ['confidential', 'non-disclosure']):
            themes.append("confidentiality requirements")
        if any(word in text_lower for word in ['benefits', 'insurance']):
            themes.append("benefits and perks")
        
        if themes:
            summary_parts.append(f"Key areas covered include: {', '.join(themes)}.")
        
        return ' '.join(summary_parts)
    
    def identify_document_type(self, text: str) -> str:
        """Identify the type of legal document"""
        text_lower = text.lower()
        
        if any(phrase in text_lower for phrase in ['employment agreement', 'employment contract', 'job offer']):
            return 'employment contract'
        elif any(phrase in text_lower for phrase in ['lease agreement', 'rental agreement', 'tenancy']):
            return 'lease agreement'
        elif any(phrase in text_lower for phrase in ['purchase agreement', 'sales contract', 'buy']):
            return 'purchase agreement'
        elif any(phrase in text_lower for phrase in ['non-disclosure', 'nda', 'confidentiality agreement']):
            return 'non-disclosure agreement'
        elif any(phrase in text_lower for phrase in ['service agreement', 'consulting agreement']):
            return 'service agreement'
        elif any(phrase in text_lower for phrase in ['partnership agreement', 'joint venture']):
            return 'partnership agreement'
        else:
            return 'legal document'
    
    def extract_key_points(self, text: str) -> List[str]:
        """Extract key points from document"""
        sentences = self.simple_sentence_tokenize(text)
        key_points = []
        
        for sentence in sentences:
            # Look for sentences with important keywords and proper length
            if (self.contains_legal_content(sentence) and 
                len(sentence.split()) > 8 and 
                len(sentence.split()) < 50):
                
                key_points.append(sentence.strip())
                
                if len(key_points) >= 6:  # Limit to top 6 key points
                    break
        
        return key_points
    
    def get_fallback_analysis(self, text: str) -> Dict:
        """Provide fallback analysis when processing fails"""
        word_count = len(text.split())
        
        return {
            'summary': f"This legal document contains {word_count} words and covers standard legal terms and conditions. The document includes various clauses that define rights, obligations, and procedures for the parties involved.",
            'clauses': [
                {
                    'title': '📄 Document Overview',
                    'original': text[:300] + '...' if len(text) > 300 else text,
                    'simplified': 'This document contains legal terms and conditions that both parties must follow.',
                    'explanation': 'Legal documents establish the rules and obligations that govern relationships between parties.'
                }
            ],
            'document_type': 'legal document',
            'key_points': [
                'Document establishes legal obligations',
                'Both parties have rights and responsibilities', 
                'Terms are legally binding when signed',
                'Standard legal procedures apply'
            ]
        }
    
    def answer_question(self, question: str, document_text: str) -> str:
        """Answer questions about the document using rule-based approach"""
        question_lower = question.lower()
        sentences = self.simple_sentence_tokenize(document_text)
        
        # Common question patterns with smart responses
        if any(word in question_lower for word in ['salary', 'pay', 'money', 'compensation']):
            salary_sentences = [s for s in sentences 
                              if any(word in s.lower() for word in ['salary', 'wage', 'compensation', 'payment'])]
            if salary_sentences:
                return f"Regarding compensation: {salary_sentences[0][:200]}... Please review the compensation section for complete details."
            else:
                return "I don't see specific salary information in this document. You may need to look for a separate compensation agreement."
        
        elif any(word in question_lower for word in ['termination', 'quit', 'leave', 'fire']):
            termination_sentences = [s for s in sentences 
                                   if any(word in s.lower() for word in ['termination', 'terminate', 'notice', 'end'])]
            if termination_sentences:
                return f"About termination: {termination_sentences[0][:200]}... Check the termination clause for complete procedures."
            else:
                return "I don't see specific termination procedures in this document."
        
        elif any(word in question_lower for word in ['benefit', 'insurance', 'vacation', 'leave']):
            benefit_sentences = [s for s in sentences 
                               if any(word in s.lower() for word in ['benefit', 'insurance', 'vacation', 'leave', 'health'])]
            if benefit_sentences:
                return f"Regarding benefits: {benefit_sentences[0][:200]}... See the benefits section for full details."
            else:
                return "I don't see specific benefit information in this document."
        
        elif any(word in question_lower for word in ['confidential', 'secret', 'disclosure']):
            conf_sentences = [s for s in sentences 
                            if any(word in s.lower() for word in ['confidential', 'disclosure', 'proprietary', 'secret'])]
            if conf_sentences:
                return f"About confidentiality: {conf_sentences[0][:200]}... Review confidentiality clauses for complete terms."
            else:
                return "I don't see specific confidentiality requirements in this document."
        
        elif any(word in question_lower for word in ['compete', 'competition', 'competitor']):
            compete_sentences = [s for s in sentences 
                               if any(word in s.lower() for word in ['compete', 'competition', 'competitor', 'restraint'])]
            if compete_sentences:
                return f"About competition restrictions: {compete_sentences[0][:200]}... Check non-compete clauses for details."
            else:
                return "I don't see specific non-compete restrictions in this document."
        
        else:
            # Generic search through document
            relevant_sentences = []
            question_words = [word.strip('.,!?;:"()[]{}').lower() for word in question.split() 
                            if len(word) > 3 and word.lower() not in ['what', 'does', 'this', 'mean', 'about']]
            
            for sentence in sentences:
                sentence_lower = sentence.lower()
                if any(word in sentence_lower for word in question_words):
                    relevant_sentences.append(sentence)
            
            if relevant_sentences:
                return f"I found this relevant information: {relevant_sentences[0][:250]}... You may want to review the complete section for more details."
            else:
                return f"I couldn't find specific information about '{question}' in the document. Try asking about compensation, termination, benefits, or other specific topics covered in the document."

# Initialize components
doc_processor = DocumentProcessor()
legal_analyzer = LegalAnalyzer()

# Store for current session (in production, use proper database)
session_data = {}

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/', methods=['POST'])
def upload_and_analyze():
    """Handle document upload and analysis"""
    try:
        # Check if file was uploaded
        if 'document' not in request.files:
            logger.error("No file in request")
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['document']
        logger.info(f"Received file: {file.filename}")
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not doc_processor.allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed. Please upload PDF, DOC, DOCX, or TXT files.'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        logger.info(f"Saving file to: {file_path}")
        file.save(file_path)
        
        # Verify file was saved
        if not os.path.exists(file_path):
            return jsonify({'error': 'Failed to save uploaded file'}), 500
        
        # Extract text from document
        document_text = doc_processor.extract_text(file_path)
        
        if not document_text.strip():
            return jsonify({'error': 'Could not extract text from document. Please ensure the file contains readable text.'}), 400
        
        if 'Error' in document_text and 'requires' in document_text:
            return jsonify({'error': document_text}), 400
        
        logger.info(f"Extracted text length: {len(document_text)} characters")
        
        # Analyze document
        analysis_result = legal_analyzer.analyze_document(document_text)
        
        # Store in session for Q&A
        session_key = timestamp
        session_data[session_key] = {
            'document_text': document_text,
            'analysis': analysis_result,
            'filename': file.filename,
            'upload_time': datetime.now()
        }
        
        # Add session key to response
        analysis_result['session_key'] = session_key
        
        # Clean up old sessions
        cleanup_old_sessions()
        
        # Clean up uploaded file (optional)
        try:
            os.remove(file_path)
        except Exception as e:
            logger.warning(f"Could not remove uploaded file: {e}")
        
        logger.info("Document analysis completed successfully")
        return jsonify(analysis_result)
    
    except Exception as e:
        logger.error(f"Error in upload_and_analyze: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Internal server error during document processing: {str(e)}'}), 500

@app.route('/ask', methods=['POST'])
def ask_question():
    """Handle Q&A about the document"""
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form
        
        question = data.get('question', '').strip()
        session_key = data.get('session_key', '')
        
        logger.info(f"Question received: {question[:50]}... Session: {session_key}")
        
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        # For demo purposes, try to find the most recent session if no key provided
        if not session_key and session_data:
            session_key = max(session_data.keys())
            logger.info(f"Using most recent session: {session_key}")
        
        if session_key not in session_data:
            return jsonify({'error': 'Document session not found. Please upload a document first.'}), 400
        
        document_text = session_data[session_key]['document_text']
        answer = legal_analyzer.answer_question(question, document_text)
        
        logger.info("Question answered successfully")
        return jsonify({'answer': answer})
    
    except Exception as e:
        logger.error(f"Error in ask_question: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Error processing question: {str(e)}'}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'ai_backend': 'Rule-based processing',
        'active_sessions': len(session_data),
        'upload_folder': app.config['UPLOAD_FOLDER'],
        'upload_folder_exists': os.path.exists(app.config['UPLOAD_FOLDER'])
    })

@app.route('/demo')
def demo_mode():
    """Demo endpoint for testing frontend without file upload"""
    demo_data = {
        'summary': "This employment contract outlines comprehensive terms of employment including salary structure, benefits package, termination procedures, and confidentiality obligations. The document establishes a 6-month probationary period, competitive health benefits, and includes standard non-compete restrictions valid for 12 months post-employment.",
        'clauses': [
            {
                'title': "📝 Employment Duties",
                'original': "The Employee shall perform such duties and responsibilities as may be assigned by the Company from time to time, and shall devote their full time and attention to the business of the Company during regular business hours.",
                'simplified': "You must focus entirely on your work duties during business hours and can't work for other companies during employment.",
                'explanation': "This is a standard exclusivity clause that ensures you dedicate your working time to this company and prevents conflicts of interest with other employers."
            },
            {
                'title': "💰 Compensation Package",
                'original': "The Company shall pay the Employee a base salary of Sixty Thousand Dollars ($60,000) per annum, payable in equal monthly installments, subject to applicable withholdings and deductions as required by law.",
                'simplified': "You'll receive $60,000 per year, paid monthly ($5,000/month), with normal taxes taken out.",
                'explanation': "Your annual salary is divided into 12 equal monthly payments with standard tax deductions and withholdings applied according to federal and state requirements."
            },
            {
                'title': "📋 Termination Procedures",
                'original': "Either party may terminate this Agreement at any time, with or without cause, upon thirty (30) days written notice to the other party, except that the Company may terminate Employee immediately for cause.",
                'simplified': "Either you or the company can end this contract with 30 days written notice, but the company can fire you immediately for serious misconduct.",
                'explanation': "This establishes termination procedures with standard notice periods, while allowing immediate termination for serious violations like theft, harassment, or policy breaches."
            },
            {
                'title': "🔒 Confidentiality Agreement",
                'original': "Employee acknowledges that during employment, Employee may have access to confidential information and trade secrets. Employee agrees not to disclose such information to any third party.",
                'simplified': "You must keep all company secrets private and not share sensitive information with anyone outside the company.",
                'explanation': "This protects the company's proprietary information, client data, and business strategies from being shared with competitors or unauthorized parties."
            }
        ],
        'document_type': 'employment contract',
        'key_points': [
            'Full-time employment with exclusivity requirements',
            'Annual salary of $60,000 paid monthly',
            '30-day notice period for standard termination',
            'Immediate termination allowed for misconduct',
            'Comprehensive confidentiality obligations',
            'Standard benefits package included'
        ],
        'session_key': 'demo_session'
    }
    
    # Store demo session
    session_data['demo_session'] = {
        'document_text': 'Demo employment contract with standard terms and conditions...',
        'analysis': demo_data,
        'filename': 'demo_contract.txt',
        'upload_time': datetime.now()
    }
    
    return jsonify(demo_data)

@app.route('/sessions')
def list_sessions():
    """List active sessions (for debugging)"""
    return jsonify({
        'active_sessions': len(session_data),
        'sessions': {k: {
            'filename': v.get('filename', 'unknown'),
            'upload_time': v.get('upload_time', 'unknown').isoformat() if isinstance(v.get('upload_time'), datetime) else str(v.get('upload_time', 'unknown')),
            'document_type': v.get('analysis', {}).get('document_type', 'unknown')
        } for k, v in session_data.items()}
    })

@app.route('/sample')
def sample_analysis():
    """Provide sample analysis for testing"""
    sample_text = """
    EMPLOYMENT AGREEMENT
    
    This Employment Agreement is entered into between XYZ Corporation (the "Company") and John Doe (the "Employee").
    
    1. POSITION AND DUTIES
    The Employee shall serve as Software Developer and shall perform such duties and responsibilities as may be assigned by the Company from time to time. Employee shall devote their full time and attention to the business of the Company.
    
    2. COMPENSATION
    The Company shall pay the Employee a base salary of Seventy-Five Thousand Dollars ($75,000) per annum, payable in equal monthly installments, subject to applicable withholdings and deductions as required by law.
    
    3. TERMINATION
    Either party may terminate this Agreement at any time, with or without cause, upon thirty (30) days written notice to the other party.
    
    4. CONFIDENTIALITY
    Employee acknowledges that during employment, Employee may have access to confidential information and trade secrets of the Company. Employee agrees not to disclose such information to any third party.
    """
    
    analysis_result = legal_analyzer.analyze_document(sample_text)
    
    # Store sample session
    session_data['sample_session'] = {
        'document_text': sample_text,
        'analysis': analysis_result,
        'filename': 'sample_contract.txt',
        'upload_time': datetime.now()
    }
    
    analysis_result['session_key'] = 'sample_session'
    return jsonify(analysis_result)

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    return jsonify({'error': 'File too large. Maximum size is 16MB. Please upload a smaller file.'}), 413

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {e}")
    return jsonify({'error': 'Internal server error. Please try again.'}), 500

# Utility functions
def cleanup_old_sessions():
    """Clean up old session data (call periodically)"""
    current_time = datetime.now()
    expired_sessions = []
    
    for session_key, session_info in list(session_data.items()):
        try:
            if session_key in ['demo_session', 'sample_session']:
                continue  # Keep demo sessions
                
            upload_time = session_info.get('upload_time', current_time)
            if (current_time - upload_time).seconds > 3600:  # Keep for 1 hour
                expired_sessions.append(session_key)
        except Exception:
            expired_sessions.append(session_key)
    
    for session_key in expired_sessions:
        try:
            del session_data[session_key]
            logger.info(f"Cleaned up expired session: {session_key}")
        except KeyError:
            pass

if __name__ == '__main__':
    # Create required directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)
    
    print("🚀 Starting LegalZen Backend Server...")
    print("📂 Make sure you have the following file structure:")
    print("   app.py")
    print("   templates/index.html")
    print("   static/style.css")
    print("   static/script.js")
    print("")
    print("🔗 Access the application at: http://localhost:5000")
    print("🧪 Test with demo data at: http://localhost:5000/demo")
    print("📊 Check health status at: http://localhost:5000/health")
    print("")
    
    # Configure for development
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
        threaded=True
    )

"""
INSTALLATION GUIDE:

1. Basic Flask setup (required):
   pip install flask

2. For PDF support:
   pip install PyPDF2

3. For DOCX support:
   pip install python-docx

QUICK START (minimal dependencies):
1. pip install flask
2. Save this as app.py
3. Create the folder structure with your HTML/CSS/JS files
4. Run: python app.py
5. Visit: http://localhost:5000

The app will work with TXT files immediately and show helpful error messages 
for PDF/DOCX files if the required libraries aren't installed.

FOLDER STRUCTURE:
project/
├── app.py
├── templates/
│   └── index.html
├── static/
│   ├── style.css
│   └── script.js
└── uploads/ (created automatically)

TROUBLESHOOTING FILE UPLOADS:

1. Check file permissions on uploads folder
2. Verify file size is under 16MB
3. Ensure file types are PDF, DOC, DOCX, or TXT
4. Check browser console for JavaScript errors
5. Monitor Flask server logs for backend errors
6. Test with /health endpoint first
7. Try /demo endpoint to test frontend without file upload
"""