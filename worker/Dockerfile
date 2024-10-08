# Use Buildx to build for different platforms, specifying the platform using --platform flag
# Example: docker buildx build --platform "linux/arm64/v8" .

# Stage 1: Build Stage
FROM --platform=${BUILDPLATFORM} mcr.microsoft.com/dotnet/sdk:7.0 AS build

# Arguments for target platform, architecture, and build platform
ARG TARGETPLATFORM
ARG TARGETARCH
ARG BUILDPLATFORM

# Display build information for troubleshooting
RUN echo "Building on $BUILDPLATFORM for $TARGETPLATFORM using architecture $TARGETARCH"

# Set the working directory for the build process
WORKDIR /source

# Copy the project file and restore dependencies for the specified architecture
COPY *.csproj ./
RUN dotnet restore --arch $TARGETARCH

# Copy the rest of the source code and publish the application
COPY . ./
RUN dotnet publish -c Release -o /app --self-contained false --no-restore --arch $TARGETARCH

# Stage 2: Runtime Stage
FROM mcr.microsoft.com/dotnet/runtime:7.0 AS runtime

# Set the working directory for the runtime environment
WORKDIR /app

# Copy the application build from the build stage
COPY --from=build /app ./

# Define the entry point to start the application
ENTRYPOINT ["dotnet", "Worker.dll"]
