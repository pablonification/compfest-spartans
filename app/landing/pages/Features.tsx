import Navigation from "@/components/Navigation";

export default function Features() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-setorin-green to-setorin-green/80 pt-16 sm:pt-20">
      <Navigation />
      
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-8 font-inter">
            Features
          </h1>
          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8 md:p-12">
            <div className="text-6xl mb-6">🚧</div>
            <h2 className="text-2xl md:text-3xl font-bold text-white mb-4">
              Coming Soon
            </h2>
            <p className="text-white/80 text-lg leading-relaxed mb-8">
              We're working hard to bring you detailed information about all the amazing features 
              Setorin has to offer. This page will showcase how you can turn your waste into wealth 
              with our innovative platform.
            </p>
            <p className="text-setorin-yellow font-semibold text-lg">
              Stay tuned for more updates!
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
