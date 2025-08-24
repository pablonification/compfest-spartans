import { NextResponse } from 'next/server';

export async function POST(request) {
  try {
    const token = request.headers.get('authorization')?.replace('Bearer ', '');
    
    if (!token || token === 'null') {
      return NextResponse.json({ error: 'Unauthorized - No valid token' }, { status: 401 });
    }
    
    const body = await request.json();
    const { type = 'system', count = 1 } = body;
    
    const backendUrl = `${process.env.NEXT_PUBLIC_CONTAINER_API_URL || 'http://backend:8000'}/notifications/admin/system`;
    
    const sampleNotifications = [];
    
    for (let i = 0; i < count; i++) {
      let notificationData = {};
      
      switch (type) {
        case 'bin_status':
          notificationData = {
            bin_id: `bin_${Math.floor(Math.random() * 1000)}`,
            bin_status: ['full', 'maintenance', 'available'][Math.floor(Math.random() * 3)],
            message: `Tong sampah ${notificationData.bin_id} sedang dalam status ${notificationData.bin_status}.`
          };
          
          const binResponse = await fetch(`${process.env.NEXT_PUBLIC_CONTAINER_API_URL || 'http://backend:8000'}/notifications/admin/bin-status`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(notificationData)
          });
          
          if (binResponse.ok) {
            const result = await binResponse.json();
            sampleNotifications.push(result);
          }
          break;
          
        case 'achievement':
          notificationData = {
            achievement_type: `Milestone ${Math.floor(Math.random() * 1000)}`,
            achievement_value: Math.floor(Math.random() * 1000) + 1,
            message: `Selamat! Anda telah mencapai ${notificationData.achievement_type} dengan nilai ${notificationData.achievement_value}.`
          };
          
          const achievementResponse = await fetch(`${process.env.NEXT_PUBLIC_CONTAINER_API_URL || 'http://backend:8000'}/notifications/admin/achievement`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(notificationData)
          });
          
          if (achievementResponse.ok) {
            const result = await achievementResponse.json();
            sampleNotifications.push(result);
          }
          break;
          
        default:
          notificationData = {
            title: `Test Notification ${i + 1}`,
            message: `Ini adalah notifikasi test ke-${i + 1} untuk keperluan development.`,
            notification_type: 'system',
            priority: Math.floor(Math.random() * 3) + 1,
            action_url: i % 2 === 0 ? 'https://example.com' : undefined,
            action_text: i % 2 === 0 ? 'Kunjungi Website' : undefined
          };
          
          const systemResponse = await fetch(backendUrl, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(notificationData)
          });
          
          if (systemResponse.ok) {
            const result = await systemResponse.json();
            sampleNotifications.push(result);
          }
      }
    }
    
    return NextResponse.json({
      message: `Berhasil membuat ${sampleNotifications.length} notifikasi sample`,
      notifications: sampleNotifications
    });
    
  } catch (error) {
    console.error('Error creating sample notifications:', error);
    return NextResponse.json(
      { error: 'Failed to create sample notifications', details: error.message },
      { status: 500 }
    );
  }
}
