import Navigation from "@/components/Navigation";

export default function About() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-setorin-green to-setorin-green/80 pt-16 sm:pt-20">
      <Navigation />
      
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-8 font-inter">
            About Us
          </h1>
          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8 md:p-12">
            <div className="text-6xl mb-6">🌱</div>
            <h2 className="text-2xl md:text-3xl font-bold text-white mb-4">
              Our Mission
            </h2>
            <p className="text-white/80 text-lg leading-relaxed mb-8">
              At Setorin, we're revolutionizing waste management by creating a platform that 
              transforms sorted waste into real money. Our mission is to make recycling 
              profitable and accessible for everyone while building a more sustainable future.
            </p>
            <p className="text-setorin-yellow font-semibold text-lg">
              Learn more about our story and team coming soon!
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
