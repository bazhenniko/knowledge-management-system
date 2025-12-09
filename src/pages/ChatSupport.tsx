import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { ArrowLeft, Calendar, Send } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface Message {
  id: number;
  text: string;
  sender: 'admin' | 'user';
  timestamp: string;
}

const ChatSupport = () => {
  const navigate = useNavigate();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      text: 'ааааааааааааааааа',
      sender: 'admin',
      timestamp: '15:08',
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = () => {
    if (!inputValue.trim()) return;

    const newMessage: Message = {
      id: messages.length + 1,
      text: inputValue,
      sender: 'user',
      timestamp: new Date().toLocaleTimeString('ru-RU', {
        hour: '2-digit',
        minute: '2-digit',
      }),
    };

    setMessages([...messages, newMessage]);
    setInputValue('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="h-screen flex flex-col bg-black text-white">
      {/* Header */}
      <div className="flex items-center gap-3 p-4 border-b border-gray-800">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate('/')}
          className="text-white hover:bg-gray-800"
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex-1">
          <h1 className="text-lg font-semibold">Подарочная коробка</h1>
          <p className="text-sm text-gray-400">Упаковщик подарков</p>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="text-white hover:bg-gray-800"
        >
          <Calendar className="h-5 w-5" />
        </Button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${
              message.sender === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div className="max-w-[80%]">
              {message.sender === 'admin' && (
                <div className="text-xs text-gray-400 mb-1">Администратор</div>
              )}
              <Card
                className={`p-3 ${
                  message.sender === 'user'
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-gray-800 text-white border-gray-700'
                }`}
              >
                <p className="break-words">{message.text}</p>
              </Card>
              <div className="text-xs text-gray-500 mt-1 px-1">
                {message.timestamp}
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-800">
        <div className="flex gap-2">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Введите сообщение..."
            className="flex-1 bg-gray-900 border-gray-700 text-white placeholder:text-gray-500 focus:border-gray-600"
          />
          <Button
            onClick={handleSend}
            disabled={!inputValue.trim()}
            className="bg-blue-600 hover:bg-blue-700"
          >
            <Send className="h-5 w-5" />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ChatSupport;
