import os
import json
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import logging
from logging.handlers import RotatingFileHandler

# Import your existing RAG Chatbot class
from rag_chatbot import UniversityRAGChatbot

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Logging Configuration
handler = RotatingFileHandler('fhnw_bot.log', maxBytes=100000, backupCount=3)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
handler.setFormatter(formatter)
app.logger.addHandler(handler)
app.logger.setLevel(logging.DEBUG)

# Initialize RAG Chatbot
chatbot = UniversityRAGChatbot()

@app.route('/api/chat', methods=['POST'])
def chat_endpoint():
    """
    Endpoint for chat interaction with the RAG chatbot
    
    Expected JSON payload:
    {
        "messages": [
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."},
            ...
        ]
    }
    
    The chatbot will use the content of the most recent message as the query.
    Returns a streaming response of the chatbot's answer.
    """
    try:
        # Get messages from the request
        data = request.get_json()
        conversation = data.get('messages', [])
        
        if not conversation:
            return jsonify({"error": "No messages provided"}), 400
        
        # Generate response stream using the query
        response_stream = chatbot.generate_response(conversation)
        
        def generate():
            """
            Generator function to stream response chunks
            """
            if response_stream:
                for chunk in response_stream:
                    if chunk.choices[0].delta.content is not None:
                        yield f"data: {json.dumps({'text': chunk.choices[0].delta.content})}\n\n"
                
                # End of stream signal
                yield "data: [DONE]\n\n"
            else:
                yield f"data: {json.dumps({'text': 'An error occurred while generating the response.'})}\n\n"
                yield "data: [DONE]\n\n"

        return Response(generate(), mimetype='text/event-stream')
    
    except Exception as e:
        app.logger.error(f"Chat API error: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(404)
def page_not_found(e):
    app.logger.error(f"404 Error: {e}, path: {request.path}", exc_info=False)
    return jsonify({"error": "Not Found", "path": request.path}), 404

@app.errorhandler(500)
def internal_server_error(e):
    app.logger.error(f"Server Error: {e}, path: {request.path}", exc_info=True)
    return jsonify({"error": "Internal Server Error", "path": request.path}), 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
