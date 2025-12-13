import React, { useState, useRef, useEffect } from 'react';
import { Send, Menu, Sprout, Plus, MessageSquare, User, Bot, Loader2, Settings, Thermometer, Droplets } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';

const ChatInterface = () => {
    const [messages, setMessages] = useState([
        { role: 'system', content: "Hello! I'm Agronus. Please fill in your soil details in the sidebar to get accurate recommendations." }
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const messagesEndRef = useRef(null);

    // Soil Parameters State
    const [soilParams, setSoilParams] = useState({
        nitrogen: 90,
        phosphorus: 42,
        potassium: 43,
        temperature: 20.8,
        humidity: 82.0,
        pH_Level: 6.5,
        rainfall: 202.9
    });

    const sampleQuestions = [
        "What crop is best for my soil?",
        "How much fertilizer should I use?",
        "Is my rainfall sufficient for Rice?",
        "Suggest a crop rotation plan."
    ];

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(scrollToBottom, [messages]);

    const handleParamChange = (e) => {
        setSoilParams({ ...soilParams, [e.target.name]: e.target.value });
    };

    const handleSampleClick = (question) => {
        setInput(question);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMessage = { role: 'user', content: input };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            // 1. Send Prediction Request (Store Context)
            const predResponse = await axios.post("http://127.0.0.1:5001/predict", soilParams);
            console.log("Prediction context set:", predResponse.data);

            // 2. Send User Query (RAG)
            const queryResponse = await axios.post("http://127.0.0.1:5001/userQuery", { text: input });
            const prompt = queryResponse.data.prompt;

            // 3. Get LLM Response
            const ragResponse = await axios.post("http://127.0.0.1:5002/chat", { prompt: prompt });

            const aiMessage = {
                role: 'ai',
                content: ragResponse.data.rag_response || "I couldn't find an answer to that."
            };

            setMessages(prev => [...prev, aiMessage]);
        } catch (error) {
            console.error("Error:", error);
            setMessages(prev => [...prev, { role: 'ai', content: "Sorry, I encountered an error connecting to the farm server." }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex h-screen bg-slate-900 text-slate-100 overflow-hidden font-sans">

            {/* Sidebar (Inputs) */}
            <AnimatePresence>
                {isSidebarOpen && (
                    <motion.div
                        initial={{ width: 0, opacity: 0 }}
                        animate={{ width: 320, opacity: 1 }}
                        exit={{ width: 0, opacity: 0 }}
                        className="bg-slate-950 border-r border-slate-800 flex flex-col z-20 shadow-xl"
                    >
                        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
                            <div className="flex items-center gap-2 text-green-500 font-bold text-xl">
                                <Sprout size={24} />
                                <span>Agronus</span>
                            </div>
                            <button
                                onClick={() => setIsSidebarOpen(false)}
                                className="md:hidden text-slate-400 hover:text-white"
                            >
                                <Menu size={20} />
                            </button>
                        </div>

                        <div className="flex-1 overflow-y-auto p-4 space-y-6">

                            {/* Actions */}
                            <button
                                onClick={() => setMessages([{ role: 'system', content: "Ready! Inputs updated." }])}
                                className="w-full bg-green-600 hover:bg-green-700 text-white p-3 rounded-lg flex items-center justify-center gap-2 transition-colors shadow-lg shadow-green-900/20 font-medium"
                            >
                                <Plus size={18} />
                                <span>New Session</span>
                            </button>

                            {/* Soil Inputs Form */}
                            <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800 space-y-4">
                                <div className="flex items-center gap-2 text-slate-300 font-semibold border-b border-slate-800 pb-2 mb-2">
                                    <Settings size={16} />
                                    <span>Soil Conditions</span>
                                </div>

                                <div className="grid grid-cols-3 gap-2">
                                    <div className="space-y-1">
                                        <label className="text-xs text-slate-500">N (Nitrogen)</label>
                                        <input name="nitrogen" type="number" value={soilParams.nitrogen} onChange={handleParamChange} className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-sm focus:border-green-500 outline-none" />
                                    </div>
                                    <div className="space-y-1">
                                        <label className="text-xs text-slate-500">P (Phosphorus)</label>
                                        <input name="phosphorus" type="number" value={soilParams.phosphorus} onChange={handleParamChange} className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-sm focus:border-green-500 outline-none" />
                                    </div>
                                    <div className="space-y-1">
                                        <label className="text-xs text-slate-500">K (Potassium)</label>
                                        <input name="potassium" type="number" value={soilParams.potassium} onChange={handleParamChange} className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-sm focus:border-green-500 outline-none" />
                                    </div>
                                </div>

                                <div className="space-y-1">
                                    <label className="text-xs text-slate-500 flex items-center gap-1"><Thermometer size={10} /> Temp (°C) & Humidity (%)</label>
                                    <div className="grid grid-cols-2 gap-2">
                                        <input name="temperature" type="number" placeholder="Temp" value={soilParams.temperature} onChange={handleParamChange} className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-sm focus:border-green-500 outline-none" />
                                        <input name="humidity" type="number" placeholder="Hum" value={soilParams.humidity} onChange={handleParamChange} className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-sm focus:border-green-500 outline-none" />
                                    </div>
                                </div>

                                <div className="space-y-1">
                                    <label className="text-xs text-slate-500 flex items-center gap-1"><Droplets size={10} /> pH & Rain (mm)</label>
                                    <div className="grid grid-cols-2 gap-2">
                                        <input name="pH_Level" type="number" placeholder="pH" value={soilParams.pH_Level} onChange={handleParamChange} className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-sm focus:border-green-500 outline-none" />
                                        <input name="rainfall" type="number" placeholder="Rain" value={soilParams.rainfall} onChange={handleParamChange} className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-sm focus:border-green-500 outline-none" />
                                    </div>
                                </div>
                            </div>

                        </div>

                        {/* Recent History */}
                        <div className="p-4 border-t border-slate-800 bg-slate-900/30">
                            <div className="flex items-center gap-3 text-slate-400 text-sm">
                                <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center border border-slate-700">
                                    <User size={16} />
                                </div>
                                <div>
                                    <p className="text-white font-medium">Active Session</p>
                                    <p className="text-xs text-green-400">Connected</p>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Main Content */}
            <div className="flex-1 flex flex-col relative w-full">
                <header className="h-16 flex items-center justify-between px-4 border-b border-slate-800 bg-slate-900/50 backdrop-blur-md z-10">
                    <div className="flex items-center gap-3">
                        {!isSidebarOpen && (
                            <button onClick={() => setIsSidebarOpen(true)} className="text-slate-400 hover:text-white transition-colors p-2 hover:bg-slate-800 rounded-lg">
                                <Menu size={24} />
                            </button>
                        )}
                        <span className="font-medium text-slate-200 text-lg">Agronus AI</span>
                    </div>
                </header>

                <main className="flex-1 overflow-y-auto p-4 md:p-6 scroll-smooth">
                    <div className="max-w-3xl mx-auto space-y-6 pb-32">
                        {messages.map((msg, idx) => (
                            <motion.div
                                key={idx}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                            >
                                {msg.role !== 'user' && (
                                    <div className="w-8 h-8 rounded-full bg-green-500/10 flex items-center justify-center text-green-500 shrink-0 mt-1 border border-green-500/20 shadow-[0_0_15px_rgba(34,197,94,0.2)]">
                                        <Bot size={18} />
                                    </div>
                                )}

                                <div
                                    className={`
                                        max-w-[85%] md:max-w-[75%] p-4 rounded-2xl shadow-sm
                                        ${msg.role === 'user'
                                            ? 'bg-green-600 text-white rounded-br-none shadow-lg shadow-green-900/20'
                                            : 'bg-slate-800 text-slate-200 rounded-bl-none border border-slate-700'}
                                    `}
                                >
                                    <p className="whitespace-pre-wrap leading-relaxed text-[15px]">{msg.content}</p>
                                </div>

                                {msg.role === 'user' && (
                                    <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-slate-300 shrink-0 mt-1 border border-slate-600">
                                        <User size={18} />
                                    </div>
                                )}
                            </motion.div>
                        ))}

                        {isLoading && (
                            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-4">
                                <div className="w-8 h-8 rounded-full bg-green-500/10 flex items-center justify-center text-green-500 shrink-0 mt-1">
                                    <Bot size={18} />
                                </div>
                                <div className="bg-slate-800 p-4 rounded-2xl rounded-bl-none border border-slate-700 flex items-center gap-2">
                                    <Loader2 size={16} className="animate-spin text-green-500" />
                                    <span className="text-slate-400 text-sm">Thinking...</span>
                                </div>
                            </motion.div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>
                </main>

                <div className="absolute bottom-0 left-0 w-full bg-gradient-to-t from-slate-900 via-slate-900 to-transparent pt-10 pb-6 px-4">
                    <div className="max-w-3xl mx-auto space-y-4">

                        {/* Sample Questions Chips */}
                        {messages.length < 3 && !isLoading && (
                            <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
                                {sampleQuestions.map((q, i) => (
                                    <button
                                        key={i}
                                        onClick={() => handleSampleClick(q)}
                                        className="whitespace-nowrap px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-full text-sm text-slate-300 hover:text-green-400 transition-colors shadow-sm"
                                    >
                                        {q}
                                    </button>
                                ))}
                            </div>
                        )}

                        <form onSubmit={handleSubmit} className="relative group">
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="Ask about crops, fertilizers, or weather..."
                                className="w-full bg-slate-800/90 backdrop-blur-md border border-slate-700 text-white rounded-full py-4 pl-6 pr-14 focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:border-green-500 transition-all shadow-xl"
                            />
                            <button
                                type="submit"
                                disabled={isLoading || !input.trim()}
                                className="absolute right-2 top-2 p-2 bg-green-600 hover:bg-green-500 text-white rounded-full transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md hover:shadow-green-500/20"
                            >
                                <Send size={18} />
                            </button>
                        </form>
                        <p className="text-center text-slate-500 text-xs">
                            Agronus AI can make mistakes. Verify important information.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ChatInterface;
