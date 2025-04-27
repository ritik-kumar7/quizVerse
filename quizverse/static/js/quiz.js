// Get topic from URL parameter
const urlParams = new URLSearchParams(window.location.search);
const topic = urlParams.get('topic') || 'math';

// DOM Elements
const questionElement = document.getElementById('question');
const optionList = document.getElementById('option-list');
const nextButton = document.getElementById('next-btn');
const prevButton = document.getElementById('prev-btn');
const progressBar = document.getElementById('progress-bar');
const questionCounter = document.getElementById('question-counter');
const topicDisplay = document.getElementById('topicDisplay');
const quizContent = document.getElementById('quiz-content');
const resultsContent = document.getElementById('results-content');
const finalScore = document.getElementById('finalScore');
const scoreDetails = document.getElementById('scoreDetails');
const performanceComment = document.getElementById('performanceComment');
const restartBtn = document.getElementById('restartBtn');
const timerElement = document.getElementById('timer');

// Quiz state
let currentQuestionIndex = 0;
let selectedAnswer = null;
let userAnswers = [];
let score = 0;
let pointsEarned = 0;
let questions = [];
let quizSubmitted = false;

// Timer state
let timeLeft = 600; // 10 minutes in seconds
let timerInterval = null;

// CSRF Token helper
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Get readable topic name
function getTopicName(topic) {
    const names = {
        math: "Mathematics",
        physics: "Physics",
        html: "HTML/CSS",
        java: "Java",
        python: "Python",
        c: "C Programming",
        biology: "Biology",
        general: "General Knowledge",
        ai: "Artificial Intelligence",
        dbms: "DBMS",
        javascript: "JavaScript",
        php: "PHP"
    };
    return names[topic] || "General Knowledge";
}

// Get random unique questions
function getRandomQuestions(questionPool, count) {
    const shuffled = [...questionPool];
    for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled.slice(0, Math.min(count, shuffled.length));
}

// Load question
function loadQuestion() {
    if (quizSubmitted) return;

    const currentQuestion = questions[currentQuestionIndex];

    // Animation effect
    questionElement.classList.add('question-animate');
    setTimeout(() => {
        questionElement.classList.remove('question-animate');
    }, 500);

    // Update question text
    questionElement.textContent = currentQuestion.question;

    // Update options
    const options = ['a', 'b', 'c', 'd'];
    options.forEach((option, index) => {
        document.getElementById(`${option}_text`).textContent = currentQuestion.options[index];
    });

    // Update selected answer if exists
    if (userAnswers[currentQuestionIndex] !== null) {
        document.getElementById(userAnswers[currentQuestionIndex]).checked = true;
        selectedAnswer = userAnswers[currentQuestionIndex];
    } else {
        document.querySelectorAll('.answer').forEach(radio => {
            radio.checked = false;
        });
        selectedAnswer = null;
    }

    // Update button states
    if (currentQuestionIndex === questions.length - 1) {
        nextButton.textContent = "Submit";
    } else {
        nextButton.textContent = "Next";
    }
    
    nextButton.disabled = selectedAnswer === null;
    prevButton.disabled = currentQuestionIndex === 0;

    // Update progress
    questionCounter.textContent = `Question ${currentQuestionIndex + 1} of ${questions.length}`;
    progressBar.style.width = `${((currentQuestionIndex + 1) / questions.length) * 100}%`;
}

// Handle option selection
optionList.addEventListener('click', (e) => {
    if (quizSubmitted) return;

    const selectedRadio = e.target.closest('li')?.querySelector('input[type="radio"]');
    if (selectedRadio) {
        selectedAnswer = selectedRadio.id;
        userAnswers[currentQuestionIndex] = selectedAnswer;
        nextButton.disabled = false;
    }
});

// Handle Next button
nextButton.addEventListener('click', () => {
    if (quizSubmitted) return;

    if (currentQuestionIndex < questions.length - 1) {
        currentQuestionIndex++;
        loadQuestion();
    } else {
        const isConfirmed = confirm("Are you sure you want to submit your answers?");
        if (isConfirmed) {
            showResults();
        }
    }
});

// Handle Previous button
prevButton.addEventListener('click', () => {
    if (quizSubmitted) return;

    if (currentQuestionIndex > 0) {
        currentQuestionIndex--;
        loadQuestion();
    }
});

// Show result screen
function showResults() {
    quizSubmitted = true;
    clearInterval(timerInterval);
    nextButton.style.display = 'none';
    prevButton.style.display = 'none';
    // Calculate score and points
    score = questions.reduce((acc, question, index) => {
        const userAnswer = userAnswers[index];
        if (userAnswer) {
            const selectedIndex = userAnswer.charCodeAt(0) - 'a'.charCodeAt(0);
            if (question.options[selectedIndex] === question.answer) {
                pointsEarned += 5;
                return acc + 1;
            }
        }
        return acc;
    }, 0);

    // Update UI
    quizContent.style.display = 'none';
    resultsContent.style.display = 'block';
    finalScore.textContent = `${score}/${questions.length}`;
    scoreDetails.textContent = `You answered ${score} questions correctly and earned ${pointsEarned} points!`;

    // Performance comments
    const percentage = (score / questions.length) * 100;
    let comment = "";
    if (percentage >= 80) {
        comment = "Excellent work! You've mastered this topic.";
    } else if (percentage >= 60) {
        comment = "Good job! You have a solid understanding.";
    } else if (percentage >= 40) {
        comment = "Not bad! With more practice you'll improve.";
    } else {
        comment = "Keep practicing! Review the material and try again.";
    }
    performanceComment.textContent = comment;

    // Send results to backend
    fetch('/update_quiz_results/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({
            score: score,
            points: pointsEarned
        })
    }).catch(error => console.error('Error updating results:', error));
}

// Restart quiz
restartBtn.addEventListener('click', () => {
    window.location.href = "/topics/";
});

// Timer functions
function startTimer() {
    updateTimerDisplay();
    timerInterval = setInterval(() => {
        timeLeft--;
        updateTimerDisplay();

        if (timeLeft <= 0) {
            clearInterval(timerInterval);
            showResults();
        }
    }, 1000);
}

function updateTimerDisplay() {
    const minutes = Math.floor(timeLeft / 60);
    const seconds = timeLeft % 60;
    timerElement.textContent = `Time Left: ${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

// Initialize the quiz
async function initQuiz() {
    topicDisplay.textContent = `Topic: ${getTopicName(topic)}`;
    
    try {
        // Increment quiz played count
        await fetch('/increment_quiz_played/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            }
        });

        // Load questions
        const response = await fetch(`/static/data/${topic}-question.json`);
        if (!response.ok) throw new Error('Questions not found');
        const allQuestions = await response.json();
        
        questions = getRandomQuestions(allQuestions, 20);
        userAnswers = Array(questions.length).fill(null);
        
        loadQuestion();
        startTimer();
    } catch (error) {
        console.error('Error initializing quiz:', error);
        questionElement.textContent = 'Failed to load questions. Please try again later.';
        nextButton.disabled = true;
        prevButton.disabled = true;
    }
}

// Start the quiz
initQuiz();