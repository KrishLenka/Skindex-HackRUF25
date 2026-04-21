import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { 
  Send, 
  Activity, 
  User, 
  Clock,
  FileText,
  Search,
  Upload,
  MessageCircle,
  Library
} from 'lucide-react';
import { Link } from 'react-router-dom';

const Header = () => {
  return (
    <header className="bg-white border-b-2 border-blue-800">
      
      {/* Main Header */}
      <div className="w-full px-4">
    <div className="w-full px-4">
        <div className="flex items-center justify-between py-4">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-blue-800 flex items-center justify-center mr-4">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-blue-800 leading-tight">
                DermAI
              </h1>
              <p className="text-sm text-gray-600 leading-tight">
                Your trusted AI dermatology consultant
              </p>
            </div>
          </div>
        </div>
        
        {/* Navigation */}
        <nav className="border-t border-gray-300 py-2">
          <div className="flex space-x-8 text-sm">
            {/* Home removed - defaults to Image Analysis */}
            <Link 
              to="/" 
              className="text-blue-800 hover:text-blue-900 font-medium py-2 border-b-2 border-transparent hover:border-blue-800"
            >
              <Upload className="w-4 h-4 inline mr-2" />
              Image Analysis
            </Link>
            <Link 
              to="/assistant" 
              className="text-blue-800 hover:text-blue-900 font-medium py-2 border-b-2 border-blue-800"
            >
              <MessageCircle className="w-4 h-4 inline mr-2" />
              Clinical Assistant
            </Link>
            <Link 
              to="/library" 
              className="text-blue-800 hover:text-blue-900 font-medium py-2 border-b-2 border-transparent hover:border-blue-800"
            >
            </Link>
          </div>
        </nav>
      </div>
    </div>
    </header>
  );
};

/*
const Sidebar = () => {
  return (
    <aside className="w-64 bg-gray-100 border-r border-gray-300">
      <div className="p-4">
        <h3 className="font-bold text-gray-800 text-sm mb-4 uppercase tracking-wide">
          Clinical Resources
        </h3>
        <ul className="space-y-2 text-sm">
          <li>
            <a href="#" className="text-blue-800 hover:underline block py-1 font-medium">
              Clinical Decision Support
            </a>
          </li>
          <li>
            <a href="#" className="text-blue-800 hover:underline block py-1">
              Drug Interaction Checker
            </a>
          </li>
          <li>
            <a href="#" className="text-blue-800 hover:underline block py-1">
              Treatment Protocols
            </a>
          </li>
          <li>
            <a href="#" className="text-blue-800 hover:underline block py-1">
              ICD-10 Code Lookup
            </a>
          </li>
        </ul>
        
        <h3 className="font-bold text-gray-800 text-sm mb-4 mt-6 uppercase tracking-wide">
          Medical References
        </h3>
        <ul className="space-y-2 text-sm">
          <li>
            <a href="#" className="text-blue-800 hover:underline block py-1">
              Clinical Practice Guidelines
            </a>
          </li>
          <li>
            <a href="#" className="text-blue-800 hover:underline block py-1">
              Diagnostic Criteria Database
            </a>
          </li>
          <li>
            <a href="#" className="text-blue-800 hover:underline block py-1">
              Evidence-Based Medicine
            </a>
          </li>
          <li>
            <a href="#" className="text-blue-800 hover:underline block py-1">
              Recent Publications
            </a>
          </li>
        </ul>
      </div>
    </aside>
  );
};
*/

const AIAssistant = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'assistant',
      content: 'I am an AI assistant trained on dermatological guidelines, diagnostic criteria, and evidence-based treatment information. I can provide insights on skin conditions, possible causes, treatment options, and guidance on when it may be appropriate to visit a healthcare professional. \n\nHow may I assist you with your skin concern today?',
      timestamp: new Date().toLocaleTimeString(),
      sessionId: 'CDS-001'
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const [chatError, setChatError] = useState('');

  const commonQueries = [
    "Differential diagnosis for erythematous scaly patches",
    "First-line treatment options for moderate acne",
    "When to refer suspicious pigmented lesions",
    "Topical corticosteroid potency classification"
  ];

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const newUserMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date().toLocaleTimeString(),
      sessionId: 'USER-001'
    };

    setMessages(prev => [...prev, newUserMessage]);
    setInputMessage('');
    setIsProcessing(true);
    setChatError('');

    // Build history for the API (exclude the initial greeting)
    const history = messages.slice(1).map(m => ({
      role: m.type === 'user' ? 'user' : 'assistant',
      content: m.content,
    }));

    try {
      const res = await fetch('/api/diagnosis-chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: inputMessage, history }),
      });

      const data = await res.json();

      if (!res.ok) {
        setChatError(data.error || 'Something went wrong. Please try again.');
      } else {
        setMessages(prev => [...prev, {
          id: Date.now() + 1,
          type: 'assistant',
          content: data.reply,
          timestamp: new Date().toLocaleTimeString(),
          sessionId: 'CDS-001'
        }]);
      }
    } catch (err) {
      setChatError('Could not reach the server. Make sure the backend is running.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleQueryClick = (query) => {
    setInputMessage(query);
  };

  return (
    <div className="min-h-screen bg-white">
      <div>
        <main className="w-full p-6">
          {/* Breadcrumb removed */}
          
          <div className="w-full">     
            <h1 className="text-2xl font-bold text-gray-900 mb-4">
              Clinical Decision Support System
            </h1>
            
            <div className="bg-yellow-50 border border-yellow-400 p-4 mb-6">
              <p className="text-yellow-800 text-sm">
                <strong>DISCLAIMER:</strong> This chatbot is intended to provide general health information and support for individuals who have not yet consulted a healthcare professional. It is not a substitute for medical advice, diagnosis, or treatment. If you have a pressing or serious health concern, you should consult a qualified healthcare provider for proper evaluation and care.
              </p>
            </div>

            <Card className="h-[600px] flex flex-col border-gray-300">
              <CardHeader className="bg-gray-50 border-b border-gray-300">
                <CardTitle className="text-base text-gray-900 flex items-center justify-between">
                  <div className="flex items-center">
                    <Activity className="w-5 h-5 text-blue-800 mr-2" />
                    Clinical Decision Support Interface
                  </div>
                  <div className="text-xs text-gray-600 bg-green-100 px-2 py-1 rounded border">
                    Session Active | Version 0.0.1
                  </div>
                </CardTitle>
              </CardHeader>

              {/* Messages Area */}
              <CardContent className="flex-1 overflow-y-auto p-4 space-y-4 bg-white">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex gap-3 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    {message.type === 'assistant' && (
                      <div className="w-10 h-10 bg-blue-800 flex items-center justify-center flex-shrink-0 text-white font-bold text-xs">
                        CDS
                      </div>
                    )}
                    
                    <div
                      className={`w-full border p-4 text-sm ${
                        message.type === 'user'
                          ? 'bg-blue-50 border-blue-200'
                          : 'bg-gray-50 border-gray-300'
                      }`}
                    >
                      <pre className="whitespace-pre-wrap font-sans leading-relaxed">{message.content}</pre>
                      <div className="flex items-center gap-2 mt-3 pt-2 border-t border-gray-200 text-xs text-gray-600">
                        <Clock className="w-3 h-3" />
                        <span>{message.timestamp}</span>
                        <span>•</span>
                        <span>Session: {message.sessionId}</span>
                      </div>
                    </div>

                    {message.type === 'user' && (
                      <div className="w-10 h-10 bg-gray-600 flex items-center justify-center flex-shrink-0">
                        <User className="w-5 h-5 text-white" />
                      </div>
                    )}
                  </div>
                ))}

                {isProcessing && (
                  <div className="flex gap-3 justify-start">
                    <div className="w-10 h-10 bg-blue-800 flex items-center justify-center flex-shrink-0 text-white font-bold text-xs">
                      CDS
                    </div>
                    <div className="bg-gray-50 border border-gray-300 p-4 text-sm">
                      <div className="flex items-center gap-2 text-gray-600">
                        <div className="w-2 h-2 bg-gray-500 rounded-full animate-pulse"></div>
                        <div className="w-2 h-2 bg-gray-500 rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
                        <div className="w-2 h-2 bg-gray-500 rounded-full animate-pulse" style={{animationDelay: '0.4s'}}></div>
                        <span className="ml-2">Processing clinical inquiry...</span>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </CardContent>

              {/* Quick Queries */}
              <div className="border-t border-gray-300 p-4 bg-gray-50">
                <div className="flex items-center gap-2 mb-3">
                  <FileText className="w-4 h-4 text-blue-800" />
                  <span className="text-sm font-medium text-gray-800">Common Clinical Queries:</span>
                </div>
                <div className="grid grid-cols-2 gap-2 mb-4">
                  {commonQueries.map((query, index) => (
                    <Button
                      key={index}
                      variant="outline"
                      size="sm"
                      onClick={() => handleQueryClick(query)}
                      className="text-xs border-gray-400 hover:border-blue-600 hover:text-blue-800 justify-start text-left h-auto py-2 px-3"
                    >
                      {query}
                    </Button>
                  ))}
                </div>
                
                {/* Error message */}
                {chatError && (
                  <div className="text-sm text-red-600 bg-red-50 border border-red-200 px-3 py-2 mb-2">
                    {chatError}
                  </div>
                )}

                {/* Input Area */}
                <div className="flex gap-2">
                  <div className="flex-1">
                    <Textarea
                      value={inputMessage}
                      onChange={(e) => setInputMessage(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder="Enter your clinical question or patient presentation details..."
                      className="min-h-[80px] resize-none border-gray-400 text-sm"
                      disabled={isProcessing}
                    />
                  </div>
                  <Button
                    onClick={handleSendMessage}
                    disabled={!inputMessage.trim() || isProcessing}
                    className="bg-blue-800 hover:bg-blue-900 self-end px-6"
                  >
                    <Send className="w-4 h-4 mr-2" />
                    Submit
                  </Button>
                </div>
                
                {/* Confidentiality notice removed as requested */}
              </div>
            </Card>
          </div>
        </main>
      </div>
    </div>
  );
};

export default AIAssistant;