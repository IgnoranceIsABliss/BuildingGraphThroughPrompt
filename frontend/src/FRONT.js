import React, { useState, useEffect, useRef } from 'react';

function OpenDashboard() {
    const [query, setQuery] = useState('');
    const [history, setHistory] = useState([]);
    const [isRecording, setIsRecording] = useState(false); // Состояние для записи
    const textareaRef = useRef(null);
    const recognitionRef = useRef(null);

    // Автоматическая подстройка высоты textarea
    const adjustHeight = () => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
        }
    };

    useEffect(() => {
        adjustHeight();
    }, [query]);

    const openDashboard = () => {
        if (query.trim() === '') {
            alert('Please enter a query.');
            return;
        }

        fetch('http://127.0.0.1:5000/open_dashboard', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query }),
        })
            .then((response) => response.json())
            .then((data) => {
                alert(data.message);
                setHistory((prevHistory) => [query, ...prevHistory.slice(0, 9)]); // Сохраняем историю (до 10 записей)
            })
            .catch((error) => {
                console.error('Error:', error);
            });
    };

    const copyToClipboard = (text) => {
        navigator.clipboard.writeText(text).then(() => {
            alert('Query copied to clipboard!');
        });
    };

    const clearInput = () => {
        setQuery('');
    };

    // Инициализация голосового ввода
    useEffect(() => {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            const recognition = new SpeechRecognition();
            recognition.lang = 'ru-RU'; // Устанавливаем русский язык
            recognition.interimResults = false;
            recognition.maxAlternatives = 1;
    
            recognition.onstart = () => {
                console.log('Speech recognition started.');
            };
    
            recognition.onresult = (event) => {
                const voiceQuery = event.results[0][0].transcript;
                setQuery((prevQuery) => `${prevQuery} ${voiceQuery}`.trim());
            };
    
            recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error); // Логирование ошибки
            };
    
            recognitionRef.current = recognition;
        } else {
            alert('Speech recognition is not supported in this browser.');
        }
    }, []);
    

    const toggleVoiceInput = () => {
        if (recognitionRef.current) {
            if (isRecording) {
                recognitionRef.current.stop();
            } else {
                recognitionRef.current.start();
            }
            setIsRecording(!isRecording); // Меняем состояние кнопки
        } else {
            alert('Speech recognition is not supported in this browser.');
        }
    };

    return (
        <div style={styles.container}>
            <h1 style={styles.heading}>Open Apache Superset Dashboard</h1>
            <div style={styles.textareaContainer}>
                <textarea
                    ref={textareaRef}
                    style={styles.textarea}
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Enter dashboard query"
                />
                <button style={styles.openButton} onClick={openDashboard}>
                    Open Dashboard
                </button>
                <button
                    style={{
                        ...styles.voiceButton,
                        backgroundColor: isRecording ? '#28a745' : '#007BFF',
                    }}
                    onClick={toggleVoiceInput}
                >
                    🎤
                </button>
                <button style={styles.clearButton} onClick={clearInput}>
                    Clear
                </button>
            </div>
            {history.length > 0 && (
                <div style={styles.history}>
                    <h2 style={styles.subHeading}>History</h2>
                    <ul style={styles.historyList}>
                        {history.map((item, index) => (
                            <li key={index} style={styles.historyItem}>
                                <span style={styles.historyText}>{item}</span>
                                <button
                                    style={styles.copyButton}
                                    onClick={() => copyToClipboard(item)}
                                >
                                    Copy
                                </button>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}

const styles = {
    container: {
        textAlign: 'center',
        marginTop: '50px',
        fontFamily: 'Arial, sans-serif',
    },
    heading: {
        marginBottom: '20px',
    },
    textareaContainer: {
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'flex-start',
        position: 'relative',
        width: '80%',
        margin: '0 auto',
    },
    textarea: {
        width: '100%',
        padding: '10px',
        fontSize: '16px',
        borderRadius: '15px',
        border: '1px solid #ccc',
        resize: 'none',
        overflow: 'hidden',
        minHeight: '40px',
    },
    openButton: {
        position: 'absolute',
        left: '10px',
        bottom: '-45px',
        padding: '10px 20px',
        fontSize: '16px',
        color: '#fff',
        backgroundColor: '#007BFF',
        border: 'none',
        borderRadius: '20px',
        cursor: 'pointer',
    },
    voiceButton: {
        position: 'absolute',
        left: '200px',
        bottom: '-45px',
        padding: '10px',
        fontSize: '16px',
        color: '#fff',
        border: 'none',
        borderRadius: '20px',
        cursor: 'pointer',
    },
    clearButton: {
        position: 'absolute',
        left: '300px',
        bottom: '-45px',
        padding: '10px',
        fontSize: '16px',
        color: '#fff',
        backgroundColor: '#dc3545',
        border: 'none',
        borderRadius: '20px',
        cursor: 'pointer',
    },
    history: {
        marginTop: '100px',
        textAlign: 'left',
        display: 'inline-block',
        width: '80%',
    },
    subHeading: {
        marginBottom: '10px',
    },
    historyList: {
        listStyleType: 'none',
        padding: 0,
        maxHeight: '200px',
        overflowY: 'auto',
        backgroundColor: '#f9f9f9',
        borderRadius: '15px',
        border: '1px solid #ccc',
        padding: '10px',
    },
    historyItem: {
        padding: '5px 0',
        borderBottom: '1px solid #e0e0e0',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    historyText: {
        display: 'block',
        width: 'calc(100% - 70px)', // Учитываем место под кнопку Copy
        whiteSpace: 'normal',
        wordWrap: 'break-word',
    },
    copyButton: {
        backgroundColor: '#28a745',
        border: 'none',
        borderRadius: '5px',
        color: '#fff',
        cursor: 'pointer',
        padding: '5px 10px',
        fontSize: '14px',
    },
};

export default OpenDashboard;
