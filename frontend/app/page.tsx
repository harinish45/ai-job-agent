'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Dashboard from '@/components/Dashboard';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
    }
  }, [router]);

  return <Dashboard />;
}
