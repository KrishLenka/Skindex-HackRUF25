import React, { useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { Progress } from './ui/progress';
import { 
  Upload, 
  Download, 
  Search, 
  User, 
  Settings, 
  Activity,
  AlertCircle,
  CheckCircle,
  Info,
  MessageCircle,
  Library
} from 'lucide-react';
import { Link } from 'react-router-dom';

const Header = () => {
  return (
    <header className="bg-white border-b-2 border-blue-800">
      {/* Top Government Bar */}
      <div className="bg-blue-800 text-white text-xs py-1">
        <div className="w-full px-4 flex justify-between items-center">
          <span>Created by Krish Lenka, Ayaan Faisal, Aarav Loomba, Wayne Zhen</span>
          <span>Dermatology Analysis Tool</span>
        </div>
      </div>
      
      {/* Main Header */}
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
              {/* Home page removed intentionally */}
              <Link
                to="/"
                className="text-blue-800 hover:text-blue-900 font-medium py-2 border-b-2 border-transparent hover:border-blue-800"
              >
                <Upload className="w-4 h-4 inline mr-2" />
                Image Analysis
              </Link>
              {/* Clinical Assistant removed */}
              <Link
                to="/library"
                className="text-blue-800 hover:text-blue-900 font-medium py-2 border-b-2 border-blue-800"
              >
              </Link>
          </div>
        </nav>
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
          UI Components
        </h3>
        <ul className="space-y-2 text-sm">
          <li>
            <a href="#buttons" className="text-blue-800 hover:underline block py-1 font-medium">
              Button Components
            </a>
          </li>
          <li>
            <a href="#forms" className="text-blue-800 hover:underline block py-1">
              Form Elements
            </a>
          </li>
          <li>
            <a href="#alerts" className="text-blue-800 hover:underline block py-1">
              Status Indicators
            </a>
          </li>
          <li>
            <a href="#cards" className="text-blue-800 hover:underline block py-1">
              Information Cards
            </a>
          </li>
        </ul>
        
        <h3 className="font-bold text-gray-800 text-sm mb-4 mt-6 uppercase tracking-wide">
          Documentation
        </h3>
        <ul className="space-y-2 text-sm">
          <li>
            <a href="#" className="text-blue-800 hover:underline block py-1">
              Implementation Guide
            </a>
          </li>
          <li>
            <a href="#" className="text-blue-800 hover:underline block py-1">
              Accessibility Standards
            </a>
          </li>
          <li>
            <a href="#" className="text-blue-800 hover:underline block py-1">
              Browser Compatibility
            </a>
          </li>
        </ul>
      </div>
    </aside>
  );
};
*/

const ComponentLibrary = () => {
  const [inputValue, setInputValue] = useState('');
  const [progress, setProgress] = useState(65);

  return (
    <div className="min-h-screen bg-white">
      <Header />
      
      <div>
        <main className="w-full p-6">
          {/* Breadcrumb removed */}
          
          <div className="w-full"> 
            <h1 className="text-2xl font-bold text-gray-900 mb-4">
              Clinical Interface Component Library
            </h1>
            
            <div className="bg-blue-50 border border-blue-200 p-4 mb-6">
              <p className="text-blue-800 text-sm">
                <strong>Component Library Version 3.2.1:</strong> Standardized user interface components 
                for clinical and research applications. All components meet Section 508 accessibility 
                requirements and healthcare industry design standards.
              </p>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
              
              {/* Button Components */}
              <Card className="border-gray-300" id="buttons">
                <CardHeader className="bg-gray-50 border-b border-gray-300">
                  <CardTitle className="text-base text-gray-900 flex items-center">
                    <Settings className="w-5 h-5 mr-2 text-blue-800" />
                    Button Components
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-4 space-y-4">
                  <div>
                    <p className="text-sm text-gray-700 mb-3 font-medium">Primary Actions:</p>
                    <div className="space-y-2">
                      <Button className="w-full bg-blue-800 hover:bg-blue-900 text-sm">
                        <Upload className="w-4 h-4 mr-2" />
                        Upload Patient Data
                      </Button>
                      
                      <Button className="w-full bg-green-700 hover:bg-green-800 text-sm">
                        <CheckCircle className="w-4 h-4 mr-2" />
                        Submit Analysis
                      </Button>
                    </div>
                  </div>

                  <div>
                    <p className="text-sm text-gray-700 mb-3 font-medium">Secondary Actions:</p>
                    <div className="space-y-2">
                      <Button variant="outline" className="w-full border-gray-400 text-gray-700 hover:bg-gray-50 text-sm">
                        <Search className="w-4 h-4 mr-2" />
                        Search Database
                      </Button>
                      
                      <Button variant="outline" className="w-full border-gray-400 text-gray-700 hover:bg-gray-50 text-sm">
                        <Download className="w-4 h-4 mr-2" />
                        Export Report
                      </Button>
                    </div>
                  </div>

                  <div>
                    <p className="text-sm text-gray-700 mb-3 font-medium">Utility Buttons:</p>
                    <div className="grid grid-cols-2 gap-2">
                      <Button size="sm" variant="outline" className="border-gray-400 text-xs">
                        <User className="w-3 h-3 mr-1" />
                        Patient
                      </Button>
                      <Button size="sm" variant="outline" className="border-gray-400 text-xs">
                        <Settings className="w-3 h-3 mr-1" />
                        Settings
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Form Components */}
              <Card className="border-gray-300" id="forms">
                <CardHeader className="bg-gray-50 border-b border-gray-300">
                  <CardTitle className="text-base text-gray-900 flex items-center">
                    <Activity className="w-5 h-5 mr-2 text-blue-800" />
                    Form Input Elements
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-4 space-y-4">
                  <div>
                    <label className="text-sm font-medium text-gray-800 mb-2 block">
                      Patient Identifier:
                    </label>
                    <Input 
                      placeholder="Enter patient ID (e.g., MRN-12345)" 
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      className="border-gray-400 text-sm"
                    />
                    <p className="text-xs text-gray-600 mt-1">
                      Use medical record number or assigned patient ID
                    </p>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium text-gray-800 mb-2 block">
                      Clinical Notes:
                    </label>
                    <Textarea 
                      placeholder="Enter clinical observations, patient history, or additional notes..."
                      className="border-gray-400 min-h-[80px] text-sm"
                    />
                    <p className="text-xs text-gray-600 mt-1">
                      Document clinical findings and observations
                    </p>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium text-gray-800 mb-2 block">
                      Search Medical Database:
                    </label>
                    <div className="relative">
                      <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-500" />
                      <Input 
                        placeholder="Search conditions, ICD codes, treatments..."
                        className="pl-10 border-gray-400 text-sm"
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Status & Alerts */}
              <Card className="border-gray-300" id="alerts">
                <CardHeader className="bg-gray-50 border-b border-gray-300">
                  <CardTitle className="text-base text-gray-900 flex items-center">
                    <AlertCircle className="w-5 h-5 mr-2 text-blue-800" />
                    Status Indicators & Alerts
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-4 space-y-4">
                  <Alert className="border-blue-300 bg-blue-50">
                    <Info className="h-4 w-4 text-blue-700" />
                    <AlertDescription className="text-blue-800 text-sm">
                      <strong>Information:</strong> Analysis processing initiated. Please wait for completion.
                    </AlertDescription>
                  </Alert>
                  
                  <Alert className="border-green-300 bg-green-50">
                    <CheckCircle className="h-4 w-4 text-green-700" />
                    <AlertDescription className="text-green-800 text-sm">
                      <strong>Success:</strong> Diagnostic analysis completed successfully. Results available.
                    </AlertDescription>
                  </Alert>
                  
                  <Alert className="border-yellow-400 bg-yellow-50">
                    <AlertCircle className="h-4 w-4 text-yellow-700" />
                    <AlertDescription className="text-yellow-800 text-sm">
                      <strong>Attention:</strong> Clinical review required before finalizing diagnosis.
                    </AlertDescription>
                  </Alert>
                  
                  <Alert className="border-red-300 bg-red-50">
                    <AlertCircle className="h-4 w-4 text-red-700" />
                    <AlertDescription className="text-red-800 text-sm">
                      <strong>Critical:</strong> Urgent clinical attention recommended based on analysis.
                    </AlertDescription>
                  </Alert>
                  
                  <div className="space-y-2 pt-2">
                    <label className="text-sm font-medium text-gray-800">
                      Analysis Progress Status:
                    </label>
                    <Progress value={progress} className="h-3 bg-gray-200" />
                    <p className="text-xs text-gray-600">{progress}% complete - Processing diagnostic algorithms</p>
                  </div>
                </CardContent>
              </Card>

              {/* Status Badges */}
              <Card className="border-gray-300">
                <CardHeader className="bg-gray-50 border-b border-gray-300">
                  <CardTitle className="text-base text-gray-900 flex items-center">
                    <CheckCircle className="w-5 h-5 mr-2 text-blue-800" />
                    Clinical Status Badges
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-4 space-y-4">
                  <div>
                    <p className="text-sm font-medium text-gray-800 mb-3">Diagnostic Categories:</p>
                    <div className="flex flex-wrap gap-2">
                      <Badge className="bg-blue-800 text-white">
                        Dermatitis
                      </Badge>
                      <Badge className="bg-green-700 text-white">
                        Benign Lesion
                      </Badge>
                      <Badge variant="outline" className="border-gray-500 text-gray-700">
                        Inflammatory
                      </Badge>
                      <Badge className="bg-red-700 text-white">
                        Malignant
                      </Badge>
                    </div>
                  </div>
                  
                  <div>
                    <p className="text-sm font-medium text-gray-800 mb-3">Clinical Status:</p>
                    <div className="flex flex-wrap gap-2">
                      <Badge className="bg-green-700">
                        <CheckCircle className="w-3 h-3 mr-1" />
                        Approved
                      </Badge>
                      <Badge className="bg-yellow-600">
                        <AlertCircle className="w-3 h-3 mr-1" />
                        Under Review
                      </Badge>
                      <Badge className="bg-red-700">
                        <AlertCircle className="w-3 h-3 mr-1" />
                        Urgent
                      </Badge>
                    </div>
                  </div>
                  
                  <div>
                    <p className="text-sm font-medium text-gray-800 mb-3">Confidence Levels:</p>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-700">High Confidence</span>
                        <Badge className="bg-green-700">95%</Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-700">Moderate Confidence</span>
                        <Badge className="bg-yellow-600">78%</Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-700">Low Confidence</span>
                        <Badge variant="outline" className="border-gray-500 text-gray-700">45%</Badge>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Information Cards */}
              <Card className="border-gray-300" id="cards">
                <CardHeader className="bg-gray-50 border-b border-gray-300">
                  <CardTitle className="text-base text-gray-900 flex items-center">
                    <Activity className="w-5 h-5 mr-2 text-blue-800" />
                    Information Display Cards
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-4 space-y-4">
                  <Card className="border-gray-300">
                    <CardHeader className="pb-2 bg-gray-50 border-b border-gray-200">
                      <CardTitle className="text-sm font-bold text-gray-900">Patient Summary</CardTitle>
                    </CardHeader>
                    <CardContent className="p-3">
                      <div className="text-xs text-gray-700 space-y-1">
                        <p><span className="font-medium">ID:</span> MRN-78901</p>
                        <p><span className="font-medium">Age:</span> 42 years</p>
                        <p><span className="font-medium">Gender:</span> Female</p>
                        <p><span className="font-medium">Diagnosis:</span> Atopic Dermatitis (L20.9)</p>
                      </div>
                    </CardContent>
                  </Card>
                  
                  <Card className="border-blue-300 bg-blue-50">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-bold text-blue-900">
                        AI Analysis Result
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-3">
                      <p className="text-xs text-blue-800">
                        <strong>Primary Diagnosis:</strong> Seborrheic Dermatitis<br />
                        <strong>Confidence:</strong> 89% | <strong>ICD-10:</strong> L21.9<br />
                        <strong>Status:</strong> Requires dermatology consultation
                      </p>
                    </CardContent>
                  </Card>
                  
                  <div className="text-center pt-2 border-t border-gray-300">
                    <p className="text-xs text-gray-600 mb-2">
                      Clinical Component Library - Healthcare Interface Standards
                    </p>
                    <Badge variant="outline" className="text-xs border-gray-500 text-gray-700">
                      Version 3.2.1 | HIPAA Compliant
                    </Badge>
                  </div>
                </CardContent>
              </Card>

              {/* Interactive Demo */}
              <Card className="border-gray-300">
                <CardHeader className="bg-gray-50 border-b border-gray-300">
                  <CardTitle className="text-base text-gray-900 flex items-center">
                    <Settings className="w-5 h-5 mr-2 text-blue-800" />
                    Interactive Component Demo
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-4 space-y-4">
                  <Button 
                    variant="outline" 
                    className="w-full border-dashed border-2 border-gray-400 hover:border-blue-600 h-16 text-sm"
                    onClick={() => setProgress(Math.min(100, progress + 15))}
                  >
                    <Upload className="w-5 h-5 text-gray-500 mb-1" />
                    <span className="text-gray-700 block text-xs">
                      Click to simulate progress update
                    </span>
                  </Button>
                  
                  <div className="grid grid-cols-2 gap-2">
                    <Button size="sm" variant="outline" className="border-gray-400 text-xs">
                      Previous Case
                    </Button>
                    <Button size="sm" variant="outline" className="border-gray-400 text-xs">
                      Next Case
                    </Button>
                  </div>
                  
                  <div className="bg-gray-100 p-3 border border-gray-300 text-center">
                    <p className="text-xs text-gray-700 mb-2">
                      <strong>System Status:</strong> All components operational<br />
                      <strong>Last Updated:</strong> September 2024
                    </p>
                    <div className="flex justify-center gap-2">
                      <Badge className="bg-green-700 text-xs">Online</Badge>
                      <Badge variant="outline" className="border-gray-500 text-gray-700 text-xs">
                        Secure
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default ComponentLibrary;