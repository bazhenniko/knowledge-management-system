import { useState, useEffect } from 'react';
import { API_ENDPOINTS } from '@/config/api';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { Loader2, Package, ShoppingCart } from 'lucide-react';

interface GiftBox {
  id: number;
  title: string;
  description: string;
  price: number;
  image_url: string;
  created_at: string;
}

interface OrderForm {
  box_id: number;
  customer_name: string;
  customer_email: string;
  customer_phone: string;
}

const GiftBoxes = () => {
  const [boxes, setBoxes] = useState<GiftBox[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedBox, setSelectedBox] = useState<GiftBox | null>(null);
  const [orderForm, setOrderForm] = useState<OrderForm>({
    box_id: 0,
    customer_name: '',
    customer_email: '',
    customer_phone: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    fetchBoxes();
  }, []);

  const fetchBoxes = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.boxes);
      if (!response.ok) throw new Error('Не удалось загрузить коробки');
      const data = await response.json();
      setBoxes(data);
    } catch (error) {
      toast({
        title: 'Ошибка',
        description: 'Не удалось загрузить подарочные коробки',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleOrderClick = (box: GiftBox) => {
    setSelectedBox(box);
    setOrderForm({ ...orderForm, box_id: box.id });
  };

  const handleSubmitOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const response = await fetch(API_ENDPOINTS.orders, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(orderForm),
      });

      if (!response.ok) throw new Error('Ошибка при создании заказа');

      toast({
        title: 'Заказ оформлен!',
        description: 'Мы свяжемся с вами в ближайшее время',
      });

      setSelectedBox(null);
      setOrderForm({
        box_id: 0,
        customer_name: '',
        customer_email: '',
        customer_phone: '',
      });
    } catch (error) {
      toast({
        title: 'Ошибка',
        description: 'Не удалось оформить заказ',
        variant: 'destructive',
      });
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white p-6">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4 flex items-center justify-center gap-3">
            <Package className="h-10 w-10" />
            Упаковщик подарков
          </h1>
          <p className="text-lg text-gray-600">
            Выберите идеальную подарочную коробку для вашего случая
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6 mb-12">
          {boxes.map((box) => (
            <Card key={box.id} className="overflow-hidden hover:shadow-xl transition-all">
              <img
                src={box.image_url}
                alt={box.title}
                className="w-full h-48 object-cover"
              />
              <div className="p-6">
                <h3 className="text-xl font-semibold mb-2">{box.title}</h3>
                <p className="text-gray-600 mb-4">{box.description}</p>
                <div className="flex items-center justify-between">
                  <span className="text-2xl font-bold">{box.price} ₽</span>
                  <Button onClick={() => handleOrderClick(box)}>
                    <ShoppingCart className="h-4 w-4 mr-2" />
                    Заказать
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>

        {selectedBox && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
            <Card className="max-w-md w-full p-6">
              <h2 className="text-2xl font-bold mb-4">Оформление заказа</h2>
              <p className="mb-4 text-gray-600">
                {selectedBox.title} — {selectedBox.price} ₽
              </p>

              <form onSubmit={handleSubmitOrder} className="space-y-4">
                <div>
                  <Label htmlFor="name">Ваше имя</Label>
                  <Input
                    id="name"
                    required
                    value={orderForm.customer_name}
                    onChange={(e) =>
                      setOrderForm({ ...orderForm, customer_name: e.target.value })
                    }
                    placeholder="Иван Иванов"
                  />
                </div>

                <div>
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    required
                    value={orderForm.customer_email}
                    onChange={(e) =>
                      setOrderForm({ ...orderForm, customer_email: e.target.value })
                    }
                    placeholder="ivan@example.com"
                  />
                </div>

                <div>
                  <Label htmlFor="phone">Телефон</Label>
                  <Input
                    id="phone"
                    type="tel"
                    required
                    value={orderForm.customer_phone}
                    onChange={(e) =>
                      setOrderForm({ ...orderForm, customer_phone: e.target.value })
                    }
                    placeholder="+7 (999) 123-45-67"
                  />
                </div>

                <div className="flex gap-3">
                  <Button
                    type="button"
                    variant="outline"
                    className="flex-1"
                    onClick={() => setSelectedBox(null)}
                    disabled={submitting}
                  >
                    Отмена
                  </Button>
                  <Button type="submit" className="flex-1" disabled={submitting}>
                    {submitting ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Оформляем...
                      </>
                    ) : (
                      'Оформить заказ'
                    )}
                  </Button>
                </div>
              </form>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
};

export default GiftBoxes;
