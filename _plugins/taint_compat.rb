# Provide the legacy taint API for Ruby 3.2+ so Liquid rendering continues to work.
if !Object.method_defined?(:tainted?)
  class Object
    def tainted?
      false
    end

    def taint
      self
    end

    def untaint
      self
    end
  end
end
