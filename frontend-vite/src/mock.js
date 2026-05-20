// Mock data for the AI dermatology application

export const mockAnalysisResults = [
  {
    id: 1,
    condition: "Atopic Dermatitis",
    confidence: 87,
    severity: "Moderate",
    description: "A chronic inflammatory skin condition characterized by dry, itchy, and inflamed skin.",
    recommendations: [
      "Apply topical corticosteroids as prescribed",
      "Use fragrance-free, hypoallergenic moisturizers daily",
      "Avoid known triggers such as harsh soaps or allergens",
      "Consult with a dermatologist for long-term management"
    ],
    affectedAreas: ["Elbow crease", "Forearm", "Wrist"],
    treatmentOptions: [
      "Topical corticosteroids",
      "Calcineurin inhibitors",
      "Antihistamines for itching",
      "Phototherapy (in severe cases)"
    ]
  },
  {
    id: 2,
    condition: "Seborrheic Dermatitis",
    confidence: 92,
    severity: "Mild",
    description: "A common inflammatory skin condition affecting areas rich in oil glands.",
    recommendations: [
      "Use medicated shampoos with ketoconazole or selenium sulfide",
      "Apply topical antifungal creams",
      "Maintain good hygiene practices",
      "Reduce stress levels"
    ],
    affectedAreas: ["Scalp", "Eyebrows", "Nasal folds"],
    treatmentOptions: [
      "Antifungal shampoos",
      "Topical corticosteroids",
      "Calcineurin inhibitors",
      "Coal tar preparations"
    ]
  }
];

export const mockPatientProfiles = [
  {
    id: "P001",
    name: "Sarah Johnson",
    age: 34,
    gender: "Female",
    medicalHistory: ["Eczema since childhood", "Seasonal allergies"],
    currentMedications: ["Topical hydrocortisone", "Antihistamines"],
    lastVisit: "2024-01-15",
    notes: "Responding well to current treatment regimen"
  },
  {
    id: "P002",
    name: "Michael Chen",
    age: 28,
    gender: "Male",
    medicalHistory: ["Acne", "No known allergies"],
    currentMedications: ["Benzoyl peroxide", "Tretinoin"],
    lastVisit: "2024-01-12",
    notes: "Improvement noted with current acne treatment"
  }
];

export const mockConditionDatabase = [
  {
    name: "Acne Vulgaris",
    category: "Inflammatory",
    prevalence: "Very Common",
    description: "A skin condition that occurs when hair follicles become plugged with oil and dead skin cells.",
    symptoms: ["Blackheads", "Whiteheads", "Pimples", "Cysts"],
    commonAreas: ["Face", "Chest", "Back", "Shoulders"],
    ageGroup: "Teenagers and young adults"
  },
  {
    name: "Psoriasis",
    category: "Autoimmune",
    prevalence: "Common",
    description: "A chronic autoimmune condition that causes the rapid buildup of skin cells.",
    symptoms: ["Red patches", "Thick scales", "Itching", "Burning sensation"],
    commonAreas: ["Elbows", "Knees", "Scalp", "Lower back"],
    ageGroup: "Adults 20-60 years"
  },
  {
    name: "Melanoma",
    category: "Skin Cancer",
    prevalence: "Less Common",
    description: "The most serious type of skin cancer that develops in melanocytes.",
    symptoms: ["Asymmetrical moles", "Irregular borders", "Color variation", "Diameter > 6mm"],
    commonAreas: ["Any area exposed to sun", "Back", "Legs", "Arms"],
    ageGroup: "Adults over 30"
  }
];

export const mockChatResponses = [
  {
    keywords: ["acne", "pimple", "breakout"],
    response: "Acne is caused by clogged pores and can be managed with proper skincare, topical treatments, and sometimes oral medications. Key tips include gentle cleansing, avoiding harsh scrubbing, and using non-comedogenic products. Would you like specific product recommendations?"
  },
  {
    keywords: ["eczema", "dermatitis", "dry", "itchy"],
    response: "Eczema management focuses on maintaining skin barrier function. Use fragrance-free moisturizers, mild cleansers, and avoid known triggers. Topical treatments may include corticosteroids or calcineurin inhibitors. What specific areas are affected?"
  },
  {
    keywords: ["mole", "spot", "cancer", "melanoma"],
    response: "Mole evaluation uses the ABCDE criteria: Asymmetry, Border irregularity, Color changes, Diameter >6mm, and Evolution over time. Any concerning changes should be evaluated immediately by a dermatologist. Have you noticed any changes recently?"
  },
  {
    keywords: ["psoriasis", "scaly", "patches"],
    response: "Psoriasis is an autoimmune condition causing thick, scaly patches. Treatment options include topical corticosteroids, vitamin D analogs, and systemic therapies for severe cases. Stress management and trigger avoidance are also important. What areas are most affected?"
  }
];

export const mockComponentShowcase = [
  {
    category: "Buttons",
    components: [
      { name: "Primary Button", type: "primary", variant: "default" },
      { name: "Secondary Button", type: "secondary", variant: "outline" },
      { name: "Upload Button", type: "upload", variant: "default", icon: "Upload" },
      { name: "Analysis Button", type: "analysis", variant: "outline", icon: "Search" }
    ]
  },
  {
    category: "Form Elements",
    components: [
      { name: "Text Input", type: "input", placeholder: "Enter patient ID..." },
      { name: "Textarea", type: "textarea", placeholder: "Medical notes..." },
      { name: "Search Input", type: "search", placeholder: "Search conditions..." }
    ]
  },
  {
    category: "Status Indicators",
    components: [
      { name: "Success Alert", type: "alert", variant: "success" },
      { name: "Warning Alert", type: "alert", variant: "warning" },
      { name: "Info Alert", type: "alert", variant: "info" },
      { name: "Progress Bar", type: "progress", value: 75 }
    ]
  }
];

export const mockImageAnalysisSteps = [
  { step: 1, label: "Image Upload", description: "Secure image upload with validation" },
  { step: 2, label: "Preprocessing", description: "Image enhancement and normalization" },
  { step: 3, label: "AI Analysis", description: "Deep learning model inference" },
  { step: 4, label: "Results Generation", description: "Confidence scoring and recommendations" },
  { step: 5, label: "Report Creation", description: "Formatted medical report generation" }
];

// Helper functions for mock data
/**
 * Retrieves a random mock analysis result.
 * @returns {Object} A random mock diagnostic result object.
 */
export const getRandomAnalysisResult = () => {
  const randomIndex = Math.floor(Math.random() * mockAnalysisResults.length);
  return mockAnalysisResults[randomIndex];
};

/**
 * Simulates a progressive analysis loading state over time.
 * @param {Function} callback - Function called with the current progress percentage (0-100).
 * @returns {number} The interval ID used for the simulation.
 */
export const simulateAnalysisProgress = (callback) => {
  let progress = 0;
  const interval = setInterval(() => {
    progress += Math.random() * 20;
    if (progress >= 100) {
      progress = 100;
      clearInterval(interval);
    }
    callback(Math.round(progress));
  }, 300);
  return interval;
};

/**
 * Searches the mock chat responses for keywords matching the given message.
 * @param {string} message - The user input message.
 * @returns {string} The appropriate canned response or a default fallback.
 */
export const findChatResponse = (message) => {
  const lowerMessage = message.toLowerCase();
  for (let response of mockChatResponses) {
    if (response.keywords.some(keyword => lowerMessage.includes(keyword))) {
      return response.response;
    }
  }
  return "I understand you're asking about dermatology. While I can provide general information, it's important to consult with a healthcare professional for personalized advice. Is there a specific skin condition you'd like to learn about?";
};