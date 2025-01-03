import { NextRequest, NextResponse } from 'next/server';

interface Message {
  role: string;
  content: string;
}

interface ChatRequest {
  messages: Message[];
}

export async function POST(req: NextRequest) {
  try {
    const { messages } = (await req.json()) as ChatRequest;

    // Begin validation
    if (!Array.isArray(messages)) {
      return NextResponse.json({ error: 'Messages should be an array.' }, { status: 400 });
    }

    if (messages.length === 0) {
      return NextResponse.json({ error: 'Messages array cannot be empty.' }, { status: 400 });
    }

    for (let i = 0; i < messages.length; i++) {
      const message = messages[i];

      if (!message || typeof message !== 'object') {
        return NextResponse.json({ error: `Message at index ${i} is invalid.` }, { status: 400 });
      }

      const { role, content } = message;

      if (typeof role !== 'string' || typeof content !== 'string') {
        return NextResponse.json({ error: `Message at index ${i} must have 'role' and 'content' as strings.` }, { status: 400 });
      }

      if (role !== 'user' && role !== 'assistant') {
        return NextResponse.json({ error: `Message at index ${i} has an invalid role '${role}'.` }, { status: 400 });
      }
    }

    const lastMessage = messages[messages.length - 1];
    if (lastMessage.role !== 'user') {
      return NextResponse.json({ error: 'The last message must be from the user.' }, { status: 400 });
    }
    // End validation

    const response = await fetch('http://localhost:5000/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ messages }),
    });

    if (!response.ok) {
      throw new Error(`API request failed with status ${response.status}`);
    }

    const stream = new TransformStream();

    response.body?.pipeTo(stream.writable);

    return new NextResponse(stream.readable, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });
  } catch (error) {
    console.error('Server error:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
