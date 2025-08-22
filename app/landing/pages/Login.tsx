import Navigation from "@/components/Navigation";

export default function Login() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-setorin-green to-setorin-green/80 pt-16 sm:pt-20">
      <Navigation />
      
      <div className="max-w-md mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-8 font-inter">
            Login
          </h1>
          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8">
            <div className="text-6xl mb-6">🔐</div>
            <h2 className="text-2xl font-bold text-white mb-4">
              Sign In
            </h2>
            <p className="text-white/80 text-lg leading-relaxed mb-8">
              The login functionality is coming soon. Get ready to access your 
              Setorin account and start converting your waste into real money!
            </p>
            <p className="text-setorin-yellow font-semibold text-lg">
              Authentication system in development
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
