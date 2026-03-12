# Layer Filtering Implementation Plan

## Completed: Phase 1 - Backend Infrastructure

### Model Changes (model.py)
✅ Added `layer: str = ""` field to `ClassDef` to store layer/group assignment
✅ Added `get_layers()` method to `Model` class to extract unique layer names

### Parser Changes (parser.py)  
✅ Updated CSV parser to read optional 4th column as layer assignment
✅ Update ClassDef creation to accept layer parameter
✅ Example CSV format now supports:
```
Type;Name;Description;Layer
Class;Client;Client app;UI
Class;APIGateway;API router;API
Class;AuthService;Auth service;Business Logic
```

### Server Changes (server.py)
✅ Updated `/api/lanes` endpoint to return `"layers": []` array with all unique layer names
✅ Existing lane filtering mechanism ready for enhancement

## In Progress: Phase 2 - UI Layer Display

### Current State
- HTML menu has `<div class="layers-list" id="layersList">` structure (already present)
- JavaScript has `updateLaneCheckboxes()` function that needs enhancement
- UI currently shows participant checkboxes (lanes), need to add layer-based filtering

### Next Steps for Phase 2

1. **Update API Response Structure**
   - Modify server to return participant→layer mapping
   - Include layer info in `/api/lanes` response

2. **Enhance UI Logic**
   - Update `updateLaneCheckboxes()` to display layer checkboxes
   - Add logic to map layer selection to participant filtering
   - Select all participants in a layer when layer checkbox is checked

3. **Layer-Based Filtering in Rendering**
   - Update svg_renderer.py to apply layer filtering to sequence diagrams
   - Filter out participants not in selected layers
   - Remove isolated messages (where source or dest is filtered out)

## Phase 3 - Example Diagrams (User Scenarios)

Once layer filtering is complete, create comprehensive sequence diagrams in `Process/` directory:

### High-Level Scenarios
- **User Story Flows**: User → System interaction showing overall feature flow
- **Environment Integration**: Software ↔ External Systems

### Design-Level Scenarios  
- **Component Interactions**: Internal component-to- component messaging
- **Authentication Flow**: Multi-layer authentication pipeline
- **Data Access Pattern**: Request through layers to database

### Structure
Each scenario will have multiple layers for filtering:
- **UI Layer**: User-facing components
- **API Layer**: REST/Interface layer  
- **Business Logic Layer**: Processing and orchestration
- **Data Access Layer**: Database and storage operations
- **External Services**: Third-party integrations

## CSV Format Example

```
Type;Name;Description;Layer
Class;WebUI;Web browser interface;UI
    Function;SubmitForm;User submits form
        Param;credentials;Login credentials
        ReturnVal;token;Auth token

Class;APIGateway;API entry point;API
    Function;Authenticate;Authenticate request
        Param;credentials;User credentials  
        ReturnVal;token;Valid token

Class;AuthService;Authentication logic;Business Logic
    Function;ValidateCredentials;Validate user
        Param;credentials;Credentials to check
        ReturnVal;valid;Is valid

Class;UserDB;User database;Data Access
    Function;QueryUser;Fetch user record
        Param;username;Username to find
        ReturnVal;user;User object

Sequence;US_001_Login;User Login Flow
    WebUI;APIGateway;Authenticate;username;password;token
    APIGateway;AuthService;ValidateCredentials;username;password;valid
    AuthService;UserDB;QueryUser;username;user
    AuthService;APIGateway;ValidateCredentials;valid
    APIGateway;WebUI;Authenticate;token
```

## Benefits of Layer Filtering

1. **Complexity Management**: Show high-level flows without implementation details
2. **Role-Based Views**: Different users see different layers
3. **Progressive Disclosure**: Start simple, zoom in to detail as needed
4. **Traceability**: Clear mapping between user stories and layers
5. **Testing**: Test engineers can focus on specific layers

## Implementation Notes

- Layers are stored with Classes, not Participants
- Filtering works by: Layer Selection → Matching Classes/Participants → Remove isolated interactions
- Backward compatible: Diagrams without layer assignments continue to work
- Multiple participants can share same layer
